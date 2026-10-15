"""Training must remain differentiable after an inference-populated cache."""
import unittest
import weakref
try:
    import torch
except ImportError:
    torch = None


@unittest.skipIf(torch is None, 'Optional training runtime requires PyTorch')
class TestTrainingBuffers(unittest.TestCase):
    def test_completed_optimizer_releases_moments_and_gradients_but_keeps_weights(self):
        from ml.training import training_buffers
        model = torch.nn.Linear(3, 2)
        optimizer = torch.optim.AdamW(model.parameters())
        model(torch.ones(1, 3)).square().sum().backward()
        optimizer.step()
        weights = [p.detach().clone() for p in model.parameters()]
        buffers = [weakref.ref(value) for state in optimizer.state.values()
                   for value in state.values() if torch.is_tensor(value)]
        self.assertTrue(buffers)
        training_buffers.release_completed_optimizer(optimizer)
        self.assertFalse(optimizer.state)
        self.assertTrue(all(ref() is None for ref in buffers))
        self.assertTrue(all(p.grad is None for p in model.parameters()))
        self.assertTrue(all(torch.equal(p, value)
                            for p, value in zip(model.parameters(), weights)))

    def test_completed_optimizer_release_is_idempotent(self):
        from ml.training import training_buffers
        optimizer = torch.optim.AdamW(torch.nn.Linear(1, 1).parameters())
        training_buffers.release_completed_optimizer(optimizer)
        training_buffers.release_completed_optimizer(optimizer)
        self.assertFalse(optimizer.state)

    def test_cached_inference_features_can_train_without_changing_values(self):
        from ml.training import training_buffers
        model = torch.nn.Sequential(torch.nn.Linear(3, 2, bias=False))
        with torch.inference_mode():
            model.register_buffer('positions', torch.tensor([[1., 2., 3.]]), persistent=False)
        weights = model[0].weight
        expected = model.positions.clone()
        with self.assertRaisesRegex(RuntimeError, 'Inference tensors'):
            model(model.positions).square().sum().backward()
        training_buffers.restore_training_buffers(model)
        model(model.positions).square().sum().backward()
        self.assertTrue(torch.isfinite(weights.grad).all())
        self.assertGreater(float(weights.grad.abs().max()), 0.)
        self.assertTrue(torch.equal(model.positions, expected))
        self.assertIs(model[0].weight, weights)
        self.assertNotIn('positions', model.state_dict())

    def test_shared_cache_identity_and_ordinary_buffers_are_preserved(self):
        from ml.training import training_buffers
        model = torch.nn.Module()
        model.register_buffer('ordinary', torch.ones(2))
        model.register_buffer('missing', None)
        with torch.inference_mode():
            cached = torch.ones(2)
        model.register_buffer('first', cached)
        model.register_buffer('second', cached)
        ordinary = model.ordinary
        training_buffers.restore_training_buffers(model)
        self.assertIs(model.first, model.second)
        self.assertIs(model.ordinary, ordinary)
        self.assertIsNone(model.missing)
        self.assertFalse(torch.is_inference(model.first))
        first = model.first
        training_buffers.restore_training_buffers(model)
        self.assertIs(model.first, first)

    def test_nemo_relative_position_cache_can_backpropagate_after_extension(self):
        try:
            from nemo.collections.asr.parts.submodules.multi_head_attention import RelPositionalEncoding
        except ImportError:
            self.skipTest('Optional NeMo training runtime required')
        from ml.training import training_buffers
        model = torch.nn.Module()
        model.positions = RelPositionalEncoding(d_model=4, dropout_rate=0.)
        model.projection = torch.nn.Linear(4, 2)
        with torch.inference_mode():
            model.positions.extend_pe(64, torch.device('cpu'))
        _, cached = model.positions(torch.ones(1, 4, 4))
        with self.assertRaisesRegex(RuntimeError, 'Inference tensors'):
            model.projection(cached).sum().backward()
        training_buffers.restore_training_buffers(model)
        _, cached = model.positions(torch.ones(1, 4, 4))
        model.projection(cached).sum().backward()
        self.assertTrue(torch.isfinite(model.projection.weight.grad).all())

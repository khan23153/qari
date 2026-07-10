// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'surah_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

_SurahModel _$SurahModelFromJson(Map<String, dynamic> json) => _SurahModel(
      surahId: (json['surah_id'] as num).toInt(),
      surahNumber: (json['surah_number'] as num).toInt(),
      name: json['name'] as String,
      nameArabic: json['name_arabic'] as String,
      nameEnglish: json['name_english'] as String,
      nameTranslation: json['name_translation'] as String,
      revelationType: json['revelation_type'] as String,
      ayahCount: (json['ayah_count'] as num).toInt(),
      revelationOrder: (json['revelation_order'] as num).toInt(),
      pageStart: (json['page_start'] as num?)?.toInt(),
      pageEnd: (json['page_end'] as num?)?.toInt(),
    );

Map<String, dynamic> _$SurahModelToJson(_SurahModel instance) =>
    <String, dynamic>{
      'surah_id': instance.surahId,
      'surah_number': instance.surahNumber,
      'name': instance.name,
      'name_arabic': instance.nameArabic,
      'name_english': instance.nameEnglish,
      'name_translation': instance.nameTranslation,
      'revelation_type': instance.revelationType,
      'ayah_count': instance.ayahCount,
      'revelation_order': instance.revelationOrder,
      'page_start': instance.pageStart,
      'page_end': instance.pageEnd,
    };

// Plain models for the Islamic Library API (`/v1/library/...`).
//
// Grades are always a named scholar's (or a Sahih compiler's inclusion). The
// app never derives a verdict of its own from them.

List<T> _list<T>(Object? raw, T Function(Map<String, dynamic>) parse) =>
    [for (final e in (raw as List<dynamic>? ?? const [])) parse(e as Map<String, dynamic>)];

List<String> _strings(Object? raw) =>
    [for (final e in (raw as List<dynamic>? ?? const [])) e as String];

enum RulingType { sahih, hasan, daif, mawdu, other }

RulingType rulingTypeOf(String? raw) => switch (raw) {
      'sahih' => RulingType.sahih,
      'hasan' => RulingType.hasan,
      'daif' => RulingType.daif,
      'mawdu' => RulingType.mawdu,
      _ => RulingType.other,
    };

/// Narrator reliability, as ruled by the cited rijal scholars.
enum Reliability {
  prophet,
  compiler,
  sahabi,
  thiqah,
  saduq,
  daif,
  matruk,
  kadhdhab,
  unknown,
}

Reliability reliabilityOf(String? raw) => Reliability.values.firstWhere(
      (r) => r.name == raw,
      orElse: () => Reliability.unknown,
    );

enum ReviewStatus { verifiedFromSource, pendingScholarReview }

ReviewStatus reviewStatusOf(String? raw) => raw == 'verified_from_source'
    ? ReviewStatus.verifiedFromSource
    : ReviewStatus.pendingScholarReview;

class LibraryPage<T> {
  const LibraryPage({
    required this.items,
    required this.total,
    required this.page,
    required this.hasNext,
  });

  factory LibraryPage.fromJson(
    Map<String, dynamic> json,
    T Function(Map<String, dynamic>) parse,
  ) =>
      LibraryPage(
        items: _list(json['items'], parse),
        total: json['total'] as int,
        page: json['page'] as int,
        hasNext: json['has_next'] as bool? ?? false,
      );

  final List<T> items;
  final int total;
  final int page;
  final bool hasNext;
}

class LibraryCategory {
  const LibraryCategory({
    required this.slug,
    required this.nameEn,
    required this.nameAr,
    required this.collectionCount,
  });

  factory LibraryCategory.fromJson(Map<String, dynamic> json) =>
      LibraryCategory(
        slug: json['slug'] as String,
        nameEn: json['name_en'] as String,
        nameAr: json['name_ar'] as String,
        collectionCount: json['collection_count'] as int,
      );

  final String slug;
  final String nameEn;
  final String nameAr;
  final int collectionCount;
}

class LibraryCollection {
  const LibraryCollection({
    required this.slug,
    required this.category,
    required this.nameEn,
    required this.nameAr,
    required this.authorEn,
    required this.authorAr,
    required this.availability,
    required this.bookCount,
    required this.tags,
    this.authorDeathAh,
    this.hadithCount,
  });

  factory LibraryCollection.fromJson(Map<String, dynamic> json) =>
      LibraryCollection(
        slug: json['slug'] as String,
        category: json['category'] as String,
        nameEn: json['name_en'] as String,
        nameAr: json['name_ar'] as String,
        authorEn: json['author_en'] as String,
        authorAr: json['author_ar'] as String,
        authorDeathAh: json['author_death_ah'] as int?,
        availability: json['availability'] as String,
        hadithCount: json['hadith_count'] as int?,
        bookCount: json['book_count'] as int? ?? 0,
        tags: _strings(json['tags']),
      );

  final String slug;
  final String category;
  final String nameEn;
  final String nameAr;
  final String authorEn;
  final String authorAr;
  final int? authorDeathAh;

  /// `remote` (readable now), `partial`, or `planned` (catalogued only).
  final String availability;
  final int? hadithCount;
  final int bookCount;
  final List<String> tags;

  bool get isReadable => availability == 'remote' && bookCount > 0;
}

class LibraryBook {
  const LibraryBook({
    required this.number,
    required this.nameEn,
    required this.hadithFirst,
    required this.hadithLast,
    required this.hadithCount,
  });

  factory LibraryBook.fromJson(Map<String, dynamic> json) => LibraryBook(
        number: json['number'] as int,
        nameEn: json['name_en'] as String,
        hadithFirst: json['hadith_first'] as int,
        hadithLast: json['hadith_last'] as int,
        hadithCount: json['hadith_count'] as int,
      );

  final int number;
  final String nameEn;
  final int hadithFirst;
  final int hadithLast;
  final int hadithCount;
}

class ScholarGrade {
  const ScholarGrade({
    required this.scholar,
    required this.grade,
    required this.rulingType,
    required this.basis,
    this.sourceBook,
    this.sourceDataset,
  });

  factory ScholarGrade.fromJson(Map<String, dynamic> json) => ScholarGrade(
        scholar: json['scholar'] as String,
        sourceBook: json['source_book'] as String?,
        sourceDataset: json['source_dataset'] as String?,
        grade: json['grade'] as String,
        rulingType: rulingTypeOf(json['ruling_type'] as String?),
        basis: json['basis'] as String? ?? 'scholar_grading',
      );

  final String scholar;
  final String? sourceBook;
  final String? sourceDataset;
  final String grade;
  final RulingType rulingType;
  final String basis;

  /// `Sahih — al-Albani`.
  String get label => '$grade — $scholar';
}

class HadithDefect {
  const HadithDefect({
    required this.cause,
    required this.causeLabelEn,
    required this.causeLabelAr,
    required this.scholar,
    required this.sourceBook,
    required this.reviewStatus,
    this.narratorId,
    this.narratorNameAr,
    this.quoteAr,
    this.explanationEn,
    this.quoteVerified = false,
    this.sourceTextAr,
  });

  factory HadithDefect.fromJson(Map<String, dynamic> json) => HadithDefect(
        cause: json['cause'] as String,
        causeLabelEn: json['cause_label_en'] as String,
        causeLabelAr: json['cause_label_ar'] as String,
        narratorId: json['narrator_id'] as String?,
        narratorNameAr: json['narrator_name_ar'] as String?,
        scholar: json['scholar'] as String,
        sourceBook: json['source_book'] as String,
        quoteAr: json['quote_ar'] as String?,
        explanationEn: json['explanation_en'] as String?,
        reviewStatus: reviewStatusOf(json['review_status'] as String?),
        quoteVerified: json['quote_verified'] as bool? ?? false,
        sourceTextAr: json['source_text_ar'] as String?,
      );

  final String cause;
  final String causeLabelEn;
  final String causeLabelAr;
  final String? narratorId;
  final String? narratorNameAr;
  final String scholar;
  final String sourceBook;
  final String? quoteAr;
  final String? explanationEn;
  final ReviewStatus reviewStatus;
  final bool quoteVerified;

  /// The full verbatim entry the quote comes from (e.g. a Taqrib entry).
  final String? sourceTextAr;
}

class IsnadNode {
  const IsnadNode({
    required this.position,
    required this.nameAr,
    required this.role,
    required this.identification,
    required this.reliability,
    this.narratorId,
    this.termAr,
    this.candidates = const [],
  });

  factory IsnadNode.fromJson(Map<String, dynamic> json) => IsnadNode(
        position: json['position'] as int,
        nameAr: json['name_ar'] as String,
        narratorId: json['narrator_id'] as String?,
        role: json['role'] as String? ?? 'narrator',
        termAr: json['term_ar'] as String?,
        identification: json['identification'] as String,
        candidates: _strings(json['candidates']),
        reliability: reliabilityOf(json['reliability'] as String?),
      );

  final int position;
  final String nameAr;
  final String? narratorId;

  /// `compiler`, `narrator` or `prophet`.
  final String role;
  final String? termAr;

  /// `explicit`, `pending_review` or `ambiguous`.
  final String identification;
  final List<String> candidates;
  final Reliability reliability;

  bool get isAmbiguous => identification == 'ambiguous';
}

class HadithTranslation {
  const HadithTranslation({
    required this.language,
    required this.text,
    required this.source,
    required this.licenseStatus,
  });

  factory HadithTranslation.fromJson(Map<String, dynamic> json) =>
      HadithTranslation(
        language: json['language'] as String,
        text: json['text'] as String,
        source: json['source'] as String,
        licenseStatus: json['license_status'] as String,
      );

  final String language;
  final String text;
  final String source;
  final String licenseStatus;
}

class HadithSummary {
  const HadithSummary({
    required this.id,
    required this.collection,
    required this.number,
    required this.matnAr,
    required this.grades,
    this.bookNumber,
    this.translationText,
  });

  factory HadithSummary.fromJson(Map<String, dynamic> json) => HadithSummary(
        id: json['id'] as String,
        collection: json['collection'] as String,
        number: json['number'] as int,
        bookNumber: json['book_number'] as int?,
        matnAr: json['matn_ar'] as String,
        translationText: json['translation_text'] as String?,
        grades: _list(json['grades'], ScholarGrade.fromJson),
      );

  final String id;
  final String collection;
  final int number;
  final int? bookNumber;
  final String matnAr;
  final String? translationText;
  final List<ScholarGrade> grades;
}

class HadithDetail {
  const HadithDetail({
    required this.id,
    required this.collectionSlug,
    required this.collectionNameEn,
    required this.collectionNameAr,
    required this.number,
    required this.bookNumber,
    required this.textAr,
    required this.grades,
    required this.defects,
    required this.chain,
    required this.gharibWords,
    required this.sourceDataset,
    required this.sourceLicense,
    required this.reviewStatus,
    this.bookNameEn,
    this.isnadAr,
    this.matnAr,
    this.compilerNoteAr,
    this.translation,
  });

  factory HadithDetail.fromJson(Map<String, dynamic> json) {
    final collection = json['collection'] as Map<String, dynamic>;
    final book = json['book'] as Map<String, dynamic>;
    final source = json['source'] as Map<String, dynamic>;
    final translation = json['translation'] as Map<String, dynamic>?;
    return HadithDetail(
      id: json['id'] as String,
      collectionSlug: collection['slug'] as String,
      collectionNameEn: collection['name_en'] as String,
      collectionNameAr: collection['name_ar'] as String,
      number: json['number'] as int,
      bookNumber: book['number'] as int,
      bookNameEn: book['name_en'] as String?,
      textAr: json['text_ar'] as String,
      isnadAr: json['isnad_ar'] as String?,
      matnAr: json['matn_ar'] as String?,
      compilerNoteAr: json['compiler_note_ar'] as String?,
      translation:
          translation == null ? null : HadithTranslation.fromJson(translation),
      grades: _list(json['grades'], ScholarGrade.fromJson),
      defects: _list(json['defects'], HadithDefect.fromJson),
      chain: _list(json['chain'], IsnadNode.fromJson),
      gharibWords: _strings(json['gharib_words']),
      sourceDataset: source['dataset'] as String,
      sourceLicense: source['license'] as String,
      reviewStatus: reviewStatusOf(json['review_status'] as String?),
    );
  }

  final String id;
  final String collectionSlug;
  final String collectionNameEn;
  final String collectionNameAr;
  final int number;
  final int bookNumber;
  final String? bookNameEn;
  final String textAr;
  final String? isnadAr;
  final String? matnAr;
  final String? compilerNoteAr;
  final HadithTranslation? translation;
  final List<ScholarGrade> grades;
  final List<HadithDefect> defects;

  /// Compiler first, the Prophet ﷺ last (transmission order).
  final List<IsnadNode> chain;
  final List<String> gharibWords;
  final String sourceDataset;
  final String sourceLicense;
  final ReviewStatus reviewStatus;

  /// The text the reader shows as the hadith body.
  String get bodyAr => matnAr ?? textAr;
}

class NarratorBrief {
  const NarratorBrief({
    required this.id,
    required this.nameAr,
    required this.nameEn,
    required this.reliability,
  });

  factory NarratorBrief.fromJson(Map<String, dynamic> json) => NarratorBrief(
        id: json['id'] as String,
        nameAr: json['name_ar'] as String,
        nameEn: json['name_en'] as String,
        reliability: reliabilityOf(json['reliability'] as String?),
      );

  final String id;
  final String nameAr;
  final String nameEn;
  final Reliability reliability;
}

class NarratorRuling {
  const NarratorRuling({
    required this.scholar,
    required this.rulingAr,
    required this.rulingEn,
    required this.reviewStatus,
    this.sourceBook,
    this.sourceTextAr,
  });

  factory NarratorRuling.fromJson(Map<String, dynamic> json) => NarratorRuling(
        scholar: json['scholar'] as String,
        sourceBook: json['source_book'] as String?,
        rulingAr: json['ruling_ar'] as String,
        rulingEn: json['ruling_en'] as String,
        reviewStatus: reviewStatusOf(json['review_status'] as String?),
        sourceTextAr: json['source_text_ar'] as String?,
      );

  final String scholar;
  final String? sourceBook;

  /// The full verbatim entry this ruling is quoted from.
  final String? sourceTextAr;
  final String rulingAr;
  final String rulingEn;
  final ReviewStatus reviewStatus;
}

class NarratorProfile {
  const NarratorProfile({
    required this.id,
    required this.nameAr,
    required this.nameEn,
    required this.reliability,
    required this.generation,
    required this.rulings,
    required this.teachers,
    required this.students,
    this.kunyaAr,
    this.tabaqah,
    this.birthYearAh,
    this.deathYearAh,
    this.deathNote,
  });

  factory NarratorProfile.fromJson(Map<String, dynamic> json) =>
      NarratorProfile(
        id: json['id'] as String,
        nameAr: json['name_ar'] as String,
        nameEn: json['name_en'] as String,
        reliability: reliabilityOf(json['reliability'] as String?),
        kunyaAr: json['kunya_ar'] as String?,
        generation: json['generation'] as String,
        tabaqah: json['tabaqah'] as int?,
        birthYearAh: json['birth_year_ah'] as int?,
        deathYearAh: json['death_year_ah'] as int?,
        deathNote: json['death_note'] as String?,
        rulings: _list(json['rulings'], NarratorRuling.fromJson),
        teachers: _list(json['teachers'], NarratorBrief.fromJson),
        students: _list(json['students'], NarratorBrief.fromJson),
      );

  final String id;
  final String nameAr;
  final String nameEn;
  final Reliability reliability;
  final String? kunyaAr;
  final String generation;
  final int? tabaqah;
  final int? birthYearAh;
  final int? deathYearAh;
  final String? deathNote;
  final List<NarratorRuling> rulings;
  final List<NarratorBrief> teachers;
  final List<NarratorBrief> students;
}

class GharibEntry {
  const GharibEntry({
    required this.id,
    required this.wordAr,
    required this.matchedForm,
    required this.rootAr,
    required this.transliteration,
    required this.glossEn,
    required this.sourceBook,
    required this.reviewStatus,
    this.definitionAr,
  });

  factory GharibEntry.fromJson(Map<String, dynamic> json) => GharibEntry(
        id: json['id'] as String,
        wordAr: json['word_ar'] as String,
        matchedForm: json['matched_form'] as String,
        rootAr: json['root_ar'] as String,
        transliteration: json['transliteration'] as String,
        glossEn: json['gloss_en'] as String,
        definitionAr: json['definition_ar'] as String?,
        sourceBook: json['source_book'] as String,
        reviewStatus: reviewStatusOf(json['review_status'] as String?),
      );

  final String id;
  final String wordAr;
  final String matchedForm;
  final String rootAr;
  final String transliteration;
  final String glossEn;
  final String? definitionAr;
  final String sourceBook;
  final ReviewStatus reviewStatus;
}

class LibrarySearchResult {
  const LibrarySearchResult({
    required this.query,
    required this.hadiths,
    required this.narrators,
    required this.collections,
  });

  factory LibrarySearchResult.fromJson(Map<String, dynamic> json) =>
      LibrarySearchResult(
        query: json['query'] as String,
        hadiths: _list(json['hadiths'], HadithSummary.fromJson),
        narrators: _list(json['narrators'], NarratorBrief.fromJson),
        collections: _list(json['collections'], LibraryCollection.fromJson),
      );

  final String query;
  final List<HadithSummary> hadiths;
  final List<NarratorBrief> narrators;
  final List<LibraryCollection> collections;

  bool get isEmpty =>
      hadiths.isEmpty && narrators.isEmpty && collections.isEmpty;
}

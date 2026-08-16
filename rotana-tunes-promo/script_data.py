"""Copy for the Rotana Tunes promo.

`VO_LINES` drives everything downstream: the voice-over is synthesised from it,
and the cut points, caption timings and effect beats are all derived from the
per-word alignments that come back from the synthesiser. Nothing in the edit is
hand-timed, so re-wording a line automatically re-times the film.

Each line carries:
  id      stable key used by the storyboard
  vo      text sent to the synthesiser (spelling tuned for pronunciation)
  pause   silence appended after the line, in seconds
  caption on-screen kinetic type; a list of "beats", each a list of words that
          pop on together. Beat i is tied to the VO word whose index is given
          by `on`, so type lands on the syllable that says it.
"""

BRAND_AR = "روتانا تيونز"
BRAND_LAT = "ROTANA TUNES"

# "تْيُونْز" phonemises to /tjuːnz/, i.e. the English word "tunes".
# Written plainly it becomes /tiːuːnz/ ("tee-oonz"), which is wrong.
BRAND_VO = "رُوتَانَا تْيُونْز"

VO_LINES = [
    {
        "id": "hook",
        "vo": "في كل لحظة، في داخلك أغنية.",
        "pause": 0.30,
        "caption": [{"on": 3, "words": ["في", "داخلك"]}, {"on": 5, "words": ["أغنية"]}],
    },
    {
        "id": "brand",
        "vo": f"{BRAND_VO}، كل الموسيقى العربية في مكان واحد.",
        "pause": 0.24,
        "caption": [{"on": 2, "words": ["كل", "الموسيقى", "العربية"]},
                    {"on": 5, "words": ["في", "مكان", "واحد"]}],
    },
    {
        "id": "library",
        "vo": "ملايين الأغاني، من الطرب الأصيل إلى أحدث الإصدارات.",
        "pause": 0.20,
        "caption": [{"on": 0, "words": ["ملايين", "الأغاني"]},
                    {"on": 2, "words": ["من", "الطرب", "الأصيل"]},
                    {"on": 5, "words": ["إلى", "أحدث", "الإصدارات"]}],
    },
    {
        "id": "taste",
        "vo": "قوائم تشغيل على مزاجك، وجودة صوت تضعك في قلب الحفلة.",
        "pause": 0.20,
        "caption": [{"on": 0, "words": ["قوائم", "تشغيل"]},
                    {"on": 2, "words": ["على", "مزاجك"]},
                    {"on": 4, "words": ["جودة", "صوت", "استثنائية"]}],
    },
    {
        "id": "offline",
        "vo": "حمل أغانيك واستمع بدون إنترنت، وبدون إعلانات.",
        "pause": 0.26,
        "caption": [{"on": 3, "words": ["بدون", "إنترنت"]},
                    {"on": 5, "words": ["بدون", "إعلانات"]}],
    },
    {
        "id": "cta",
        "vo": f"{BRAND_VO}، حمل التطبيق الآن، وخل الموسيقى تبدأ.",
        "pause": 1.15,
        "caption": [{"on": 2, "words": ["حمّل", "التطبيق", "الآن"]}],
    },
]

# End-card lines, rendered as static design rather than kinetic beats.
CTA_HEADLINE = "حمّل التطبيق الآن"
CTA_SUB = "متاح الآن على متجري آبل وجوجل بلاي"

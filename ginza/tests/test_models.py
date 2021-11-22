import spacy
import pytest
from copy import deepcopy

from ginza import set_split_mode


MODELS = ["ja_ginza", "ja_ginza_electra"]

TOKENIZER_TESTS = [
    ("銀座でランチをご一緒しましょう。", ["銀座", "で", "ランチ", "を", "ご", "一緒", "し", "ましょう", "。"]),
    ("すもももももももものうち", ["すもも", "も", "もも", "も", "もも", "の", "うち"]),
]

COMPOUND_SPLITER_TESTS = [
    ("選挙管理委員会", 4, 3, 1),
    ("客室乗務員", 3, 2, 1),
    ("労働者協同組合", 4, 3, 1),
    ("機能性食品", 3, 2, 1),
]

TAG_TESTS = [
    ("銀座でランチをご一緒しましょう。", ["名詞-固有名詞-地名-一般", "助詞-格助詞", "名詞-普通名詞-一般", "助詞-格助詞", "接頭辞", "名詞-普通名詞-サ変可能", "動詞-非自立可能", "助動詞", "補助記号-句点"]),
    ("すもももももももものうち", ["名詞-普通名詞-一般", "助詞-係助詞", "名詞-普通名詞-一般", "助詞-係助詞", "名詞-普通名詞-一般", "助詞-格助詞", "名詞-普通名詞-副詞可能"]),
]

POS_TESTS_JA_GINZA = [
    ("銀座でランチをご一緒しましょう。", ["PROPN", "ADP", "NOUN", "ADP", "NOUN", "NOUN", "AUX", "AUX", "PUNCT"]),
    ("すもももももももものうち", ["NOUN", "ADP", "NOUN", "ADP", "NOUN", "ADP", "NOUN"]),
]

POS_TESTS_JA_GINZA_ELECTRA = [
    ("銀座でランチをご一緒しましょう。", ["PROPN", "ADP", "NOUN", "ADP", "NOUN", "VERB", "AUX", "AUX", "PUNCT"]),
    ("すもももももももものうち", ["NOUN", "ADP", "NOUN", "ADP", "NOUN", "ADP", "NOUN"]),
]

LEMMATIZE_TESTS = [
    ("新しく", "新しい"),
    ("いただきました", "いただく"),
    ("なった", "なる"),
]

NORMALIZE_TESTS = [
    ("かつ丼", "カツ丼"),
    ("附属", "付属"),
    ("SUMMER", "サマー"),
    ("シュミレーション", "シミュレーション"),
]

EMPTYISH_TESTS = [
    ("", 0),
    ("         ", 1),
    ("\n\n\t\t\n\n", 1),
    ("\r\n\r\n", 1),
    ("\n&nbsp;\n\n", 5),
]

NAUGHTY_STRINGS = [
    # ASCII punctuation
    r",./;'[]\-=",
    r'<>?:"{}|_+',
    r'!@#$%^&*()`~"',
    # Unicode additional control characters, byte order marks
    r"­؀؁؂؃؄؅؜۝܏᠎​‌‍‎‏‪",
    r"￾",
    # Unicode Symbols
    r"Ω≈ç√∫˜µ≤≥÷",
    r"åß∂ƒ©˙∆˚¬…æ",
    "œ∑´®†¥¨ˆøπ“‘",
    r"¡™£¢∞§¶•ªº–≠",
    r"¸˛Ç◊ı˜Â¯˘¿",
    r"ÅÍÎÏ˝ÓÔÒÚÆ☃",
    r"Œ„´‰ˇÁ¨ˆØ∏”’",
    r"`⁄€‹›ﬁﬂ‡°·‚—±",
    r"⅛⅜⅝⅞",
    r"ЁЂЃЄЅІЇЈЉЊЋЌЍЎЏАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдежзийклмнопрстуфхцчшщъыьэюя",
    r"٠١٢٣٤٥٦٧٨٩",
    # Unicode Subscript/Superscript/Accents
    r"⁰⁴⁵",
    r"₀₁₂",
    r"⁰⁴⁵₀₁₂",
    r"ด้้้้้็็็็็้้้้้็็็็็้้้้้้้้็็็็็้้้้้็็็็็้้้้้้้้็็็็็้้้้้็็็็็้้้้้้้้็็็็็้้้้้็็็็ ด้้้้้็็็็็้้้้้็็็็็้้้้้้้้็็็็็้้้้้็็็็็้้้้้้้้็็็็็้้้้้็็็็็้้้้้้้้็็็็็้้้้้็็็็ ด้้้้้็็็็็้้้้้็็็็็้้้้้้้้็็็็็้้้้้็็็็็้้้้้้้้็็็็็้้้้้็็็็็้้้้้้้้็็็็็้้้้้็็็็",
    r" ̄  ̄",
    # Two-Byte Characters
    r"田中さんにあげて下さい",
    r"パーティーへ行かないか",
    r"和製漢語",
    r"部落格",
    r"사회과학원 어학연구소",
    r"찦차를 타고 온 펲시맨과 쑛다리 똠방각하",
    r"社會科學院語學研究所",
    r"울란바토르",
    r"𠜎𠜱𠝹𠱓𠱸𠲖𠳏",
    # Japanese Emoticons
    r"ヽ༼ຈل͜ຈ༽ﾉ ヽ༼ຈل͜ຈ༽ﾉ",
    r"(｡◕ ∀ ◕｡)",
    r"｀ｨ(´∀｀∩",
    r"__ﾛ(,_,*)",
    r"・(￣∀￣)・:*:",
    r"ﾟ･✿ヾ╲(｡◕‿◕｡)╱✿･ﾟ",
    r",。・:*:・゜’( ☻ ω ☻ )。・:*:・゜’",
    r"(╯°□°）╯︵ ┻━┻)" "(ﾉಥ益ಥ）ﾉ﻿ ┻━┻",
    r"┬─┬ノ( º _ ºノ)",
    r"( ͡° ͜ʖ ͡°)",
    # Emoji
    r"😍",
    r"👩🏽",
    r"👾 🙇 💁 🙅 🙆 🙋 🙎 🙍",
    r"🐵 🙈 🙉 🙊",
    r"❤️ 💔 💌 💕 💞 💓 💗 💖 💘 💝 💟 💜 💛 💚 💙",
    r"✋🏿 💪🏿 👐🏿 🙌🏿 👏🏿 🙏🏿",
    r"🚾 🆒 🆓 🆕 🆖 🆗 🆙 🏧",
    r"0️⃣ 1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟",
    # Regional Indicator Symbols
    r"🇺🇸🇷🇺🇸 🇦🇫🇦🇲🇸",
    r"🇺🇸🇷🇺🇸🇦🇫🇦🇲",
    r"🇺🇸🇷🇺🇸🇦",
    # Unicode Numbers
    r"１２３",
    r"١٢٣",
    # Right-To-Left Strings
    r"ثم نفس سقطت وبالتحديد،, جزيرتي باستخدام أن دنو. إذ هنا؟ الستار وتنصيب كان. أهّل ايطاليا، بريطانيا-فرنسا قد أخذ. سليمان، إتفاقية بين ما, يذكر الحدود أي بعد, معاملة بولندا، الإطلاق عل إيو.",
    r"إيو.",
    r"בְּרֵאשִׁית, בָּרָא אֱלֹהִים, אֵת הַשָּׁמַיִם, וְאֵת הָאָרֶץ",
    r"הָיְתָהtestالصفحات التّحول",
    r"﷽",
    r"ﷺ",
    r"مُنَاقَشَةُ سُبُلِ اِسْتِخْدَامِ اللُّغَةِ فِي النُّظُمِ الْقَائِمَةِ وَفِيم يَخُصَّ التَّطْبِيقَاتُ الْحاسُوبِيَّةُ،",
    # Trick Unicode
    r"‪‪test‪",
    r"‫test",
    r" test ",
    r"test⁠test",
    r"⁦test⁧",
    # Zalgo Text
    r"Ṱ̺̺̕o͞ ̷i̲̬͇̪͙n̝̗͕v̟̜̘̦͟o̶̙̰̠kè͚̮̺̪̹̱̤ ̖t̝͕̳̣̻̪͞h̼͓̲̦̳̘̲e͇̣̰̦̬͎ ̢̼̻̱̘h͚͎͙̜̣̲ͅi̦̲̣̰̤v̻͍e̺̭̳̪̰-m̢iͅn̖̺̞̲̯̰d̵̼̟͙̩̼̘̳ ̞̥̱̳̭r̛̗̘e͙p͠r̼̞̻̭̗e̺̠̣͟s̘͇̳͍̝͉e͉̥̯̞̲͚̬͜ǹ̬͎͎̟̖͇̤t͍̬̤͓̼̭͘ͅi̪̱n͠g̴͉ ͏͉ͅc̬̟h͡a̫̻̯͘o̫̟̖͍̙̝͉s̗̦̲.̨̹͈̣",
    r"̡͓̞ͅI̗̘̦͝n͇͇͙v̮̫ok̲̫̙͈i̖͙̭̹̠̞n̡̻̮̣̺g̲͈͙̭͙̬͎ ̰t͔̦h̞̲e̢̤ ͍̬̲͖f̴̘͕̣è͖ẹ̥̩l͖͔͚i͓͚̦͠n͖͍̗͓̳̮g͍ ̨o͚̪͡f̘̣̬ ̖̘͖̟͙̮c҉͔̫͖͓͇͖ͅh̵̤̣͚͔á̗̼͕ͅo̼̣̥s̱͈̺̖̦̻͢.̛̖̞̠̫̰",
    r"̗̺͖̹̯͓Ṯ̤͍̥͇͈h̲́e͏͓̼̗̙̼̣͔ ͇̜̱̠͓͍ͅN͕͠e̗̱z̘̝̜̺͙p̤̺̹͍̯͚e̠̻̠͜r̨̤͍̺̖͔̖̖d̠̟̭̬̝͟i̦͖̩͓͔̤a̠̗̬͉̙n͚͜ ̻̞̰͚ͅh̵͉i̳̞v̢͇ḙ͎͟-҉̭̩̼͔m̤̭̫i͕͇̝̦n̗͙ḍ̟ ̯̲͕͞ǫ̟̯̰̲͙̻̝f ̪̰̰̗̖̭̘͘c̦͍̲̞͍̩̙ḥ͚a̮͎̟̙͜ơ̩̹͎s̤.̝̝ ҉Z̡̖̜͖̰̣͉̜a͖̰͙̬͡l̲̫̳͍̩g̡̟̼̱͚̞̬ͅo̗͜.̟",
    r"̦H̬̤̗̤͝e͜ ̜̥̝̻͍̟́w̕h̖̯͓o̝͙̖͎̱̮ ҉̺̙̞̟͈W̷̼̭a̺̪͍į͈͕̭͙̯̜t̶̼̮s̘͙͖̕ ̠̫̠B̻͍͙͉̳ͅe̵h̵̬͇̫͙i̹͓̳̳̮͎̫̕n͟d̴̪̜̖ ̰͉̩͇͙̲͞ͅT͖̼͓̪͢h͏͓̮̻e̬̝̟ͅ ̤̹̝W͙̞̝͔͇͝ͅa͏͓͔̹̼̣l̴͔̰̤̟͔ḽ̫.͕",
    r"Z̮̞̠͙͔ͅḀ̗̞͈̻̗Ḷ͙͎̯̹̞͓G̻O̭̗̮",
    # Unicode Upsidedown
    r"˙ɐnbᴉlɐ ɐuƃɐɯ ǝɹolop ʇǝ ǝɹoqɐl ʇn ʇunpᴉpᴉɔuᴉ ɹodɯǝʇ poɯsnᴉǝ op pǝs 'ʇᴉlǝ ƃuᴉɔsᴉdᴉpɐ ɹnʇǝʇɔǝsuoɔ 'ʇǝɯɐ ʇᴉs ɹolop ɯnsdᴉ ɯǝɹo˥",
    r"00˙Ɩ$-",
    # Unicode font
    r"Ｔｈｅ ｑｕｉｃｋ ｂｒｏｗｎ ｆｏｘ ｊｕｍｐｓ ｏｖｅｒ ｔｈｅ ｌａｚｙ ｄｏｇ",
    r"𝐓𝐡𝐞 𝐪𝐮𝐢𝐜𝐤 𝐛𝐫𝐨𝐰𝐧 𝐟𝐨𝐱 𝐣𝐮𝐦𝐩𝐬 𝐨𝐯𝐞𝐫 𝐭𝐡𝐞 𝐥𝐚𝐳𝐲 𝐝𝐨𝐠",
    r"𝕿𝖍𝖊 𝖖𝖚𝖎𝖈𝖐 𝖇𝖗𝖔𝖜𝖓 𝖋𝖔𝖝 𝖏𝖚𝖒𝖕𝖘 𝖔𝖛𝖊𝖗 𝖙𝖍𝖊 𝖑𝖆𝖟𝖞 𝖉𝖔𝖌",
    r"𝑻𝒉𝒆 𝒒𝒖𝒊𝒄𝒌 𝒃𝒓𝒐𝒘𝒏 𝒇𝒐𝒙 𝒋𝒖𝒎𝒑𝒔 𝒐𝒗𝒆𝒓 𝒕𝒉𝒆 𝒍𝒂𝒛𝒚 𝒅𝒐𝒈",
    r"𝓣𝓱𝓮 𝓺𝓾𝓲𝓬𝓴 𝓫𝓻𝓸𝔀𝓷 𝓯𝓸𝔁 𝓳𝓾𝓶𝓹𝓼 𝓸𝓿𝓮𝓻 𝓽𝓱𝓮 𝓵𝓪𝔃𝔂 𝓭𝓸𝓰",
    r"𝕋𝕙𝕖 𝕢𝕦𝕚𝕔𝕜 𝕓𝕣𝕠𝕨𝕟 𝕗𝕠𝕩 𝕛𝕦𝕞𝕡𝕤 𝕠𝕧𝕖𝕣 𝕥𝕙𝕖 𝕝𝕒𝕫𝕪 𝕕𝕠𝕘",
    r"𝚃𝚑𝚎 𝚚𝚞𝚒𝚌𝚔 𝚋𝚛𝚘𝚠𝚗 𝚏𝚘𝚡 𝚓𝚞𝚖𝚙𝚜 𝚘𝚟𝚎𝚛 𝚝𝚑𝚎 𝚕𝚊𝚣𝚢 𝚍𝚘𝚐",
    r"⒯⒣⒠ ⒬⒰⒤⒞⒦ ⒝⒭⒪⒲⒩ ⒡⒪⒳ ⒥⒰⒨⒫⒮ ⒪⒱⒠⒭ ⒯⒣⒠ ⒧⒜⒵⒴ ⒟⒪⒢",
    # File paths
    r"../../../../../../../../../../../etc/passwd%00",
    r"../../../../../../../../../../../etc/hosts",
    # iOS Vulnerabilities
    r"Powerلُلُصّبُلُلصّبُررً ॣ ॣh ॣ ॣ冗",
    r"🏳0🌈️",
]


@pytest.fixture(scope="module")
def nlp(request):
    return spacy.load(request.param)


@pytest.mark.parametrize("nlp", MODELS, indirect=True)
@pytest.mark.parametrize("text, expected_tokens", TOKENIZER_TESTS)
def test_tokenize(nlp, text, expected_tokens):
    tokens = [token.text for token in nlp(text)]
    assert tokens == expected_tokens


@pytest.mark.parametrize("nlp", MODELS, indirect=True)
@pytest.mark.parametrize("text, len_a, len_b, len_c", COMPOUND_SPLITER_TESTS)
def test_compound_spliter(nlp, text, len_a, len_b, len_c):
    assert len(nlp(text)) == len_c
    for split_mode, l in zip(["A", "B", "C"], [len_a, len_b, len_c]):
        nlp = deepcopy(nlp)
        set_split_mode(nlp, split_mode)
        assert len(nlp(text)) == l


@pytest.mark.parametrize("nlp", MODELS, indirect=True)
@pytest.mark.parametrize("text, expected_tags", TAG_TESTS)
def test_tag(nlp, text, expected_tags):
    tags = [token.tag_ for token in nlp(text)]
    assert tags == expected_tags


@pytest.mark.parametrize("nlp", ["ja_ginza"], indirect=True)
@pytest.mark.parametrize("text, expected_poss", POS_TESTS_JA_GINZA)
def test_pos_ja_ginza(nlp, text, expected_poss):
    poss = [token.pos_ for token in nlp(text)]
    assert poss == expected_poss


@pytest.mark.parametrize("nlp", ["ja_ginza_electra"], indirect=True)
@pytest.mark.parametrize("text, expected_poss", POS_TESTS_JA_GINZA_ELECTRA)
def test_pos_ja_ginza_electra(nlp, text, expected_poss):
    poss = [token.pos_ for token in nlp(text)]
    assert poss == expected_poss


@pytest.mark.parametrize("nlp", MODELS, indirect=True)
@pytest.mark.parametrize("text, lemma", LEMMATIZE_TESTS)
def test_lemmatize(nlp, text, lemma):
    doc = nlp(text)
    assert lemma == doc[0].lemma_


@pytest.mark.parametrize("nlp", MODELS, indirect=True)
@pytest.mark.parametrize("text, norm", NORMALIZE_TESTS)
def test_normalize(nlp, text, norm):
    doc = nlp(text)
    assert norm == doc[0].norm_


@pytest.mark.parametrize("nlp", MODELS, indirect=True)
@pytest.mark.parametrize("text, expected_len", EMPTYISH_TESTS)
def test_emptyish_texts(nlp, text, expected_len):
    doc = nlp(text)
    assert len(doc) == expected_len


@pytest.mark.parametrize("nlp", MODELS, indirect=True)
@pytest.mark.parametrize("text", NAUGHTY_STRINGS)
def test_naughty_strings(nlp, text):
    doc = nlp(text)
    assert doc.text_with_ws == text

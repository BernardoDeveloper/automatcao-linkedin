from linkedin_ia.little import commentary


def test_plain_text_passes_through():
    assert commentary("Olá, mundo.\n\n1. Um\n2. Dois") == "Olá, mundo.\n\n1. Um\n2. Dois"


def test_every_reserved_character_is_escaped():
    assert commentary("a|b{c}d@e[f]g(h)i<j>k\\l*m_n~o") == (
        "a\\|b\\{c\\}d\\@e\\[f\\]g\\(h\\)i\\<j\\>k\\\\l\\*m\\_n\\~o"
    )


def test_hashtags_become_hashtag_templates():
    assert commentary("#IA #ClaudeCode #Gratidão") == (
        "{hashtag|\\#|IA} {hashtag|\\#|ClaudeCode} {hashtag|\\#|Gratidão}"
    )


def test_a_hash_inside_a_word_or_before_a_space_is_text():
    assert commentary("C# e o item #1") == "C\\# e o item {hashtag|\\#|1}"
    assert commentary("# sozinho") == "\\# sozinho"


def test_a_hashtag_at_line_start_and_before_punctuation():
    assert commentary("Fim.\n#IA.") == "Fim.\n{hashtag|\\#|IA}."


def test_an_email_style_at_sign_is_text_not_a_mention():
    assert commentary("fale com @fulano") == "fale com \\@fulano"

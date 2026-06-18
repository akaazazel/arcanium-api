from app.utils.notes import encrypt, decrypt


def test_encrypt_decrypt():
    plain_text = "This is a plain text"

    encrypted_text = encrypt(plain_text)
    decryted_text = decrypt(encrypted_text)

    assert plain_text == decryted_text


def test_encrypt_same_strings():
    plain_text = "This is a plain text"
    encrypted_text_1 = encrypt(plain_text)
    encrypted_text_2 = encrypt(plain_text)

    assert encrypted_text_1 != encrypted_text_2

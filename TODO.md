resnet34 vagy vgg(16)/(8)

imageNet tanított verzió => finomhangolás

augmentation:
- fekete háttér + kivágott kör
- forgatás
- középpont mozgatás picit
- blur

kínai karakter felismerő háló => le lehet-e tölteni => kép -> karakter => utolsó réteg eldobása (fully) -> global pooling után -> saját

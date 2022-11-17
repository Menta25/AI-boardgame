1. nagy tileok (1.3-1.4) -> 1 kör felismerése -> kör bounding box * szorzó kivágás (max 20%) -> hálóba -> ha None -> elhisszük
                                              -> ha nincs kör => üres tile
                                              -> ha több kör => natúrba hálóba (no kör bounding box !!!)

stockfish (state-of-the-art sakkbot)
    alfa-béta fa keresés -> levélnode-okon -> ezek kiértékelése

=> történhet nn-nel : nnue -> hogy tanítják ezeket <-> ezt összehasonlítani az alphazero tanításával

https://en.wikipedia.org/wiki/Efficiently_updatable_neural_network
    - alfa-béta fa

class weight -> loss fgv-ben 
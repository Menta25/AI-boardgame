1. Üres képosztály -> dataset bővítés: nagjából üres, de belelóg más darab vagy ellenőrzés hough transformmal
2. FEN notation board state-ből
3. process hívás stdin/stdout (fairyfish -> ucci -> position FEN -> go depth PARAM1 movetime PARAM2 (config)) 
    - return stdout utolsó sor -> bestmove (xxxx) -> update boardstate + robotkommand ()
4. robotintegráció + tesztek

stockfish (state-of-the-art sakkbot)
    alfa-béta fa keresés -> levélnode-okon -> ezek kiértékelése

=> történhet nn-nel : nnue -> hogy tanítják ezeket <-> ezt összehasonlítani az alphazero tanításával

https://en.wikipedia.org/wiki/Efficiently_updatable_neural_network
    - alfa-béta fa

class weight -> loss fgv-ben 
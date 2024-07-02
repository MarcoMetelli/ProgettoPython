import random
import string
from imdb import Cinemagoer, IMDbError
from datetime import datetime
import textwrap
import time
import sys


class Config:
    def __init__(self, difficulty=["facile", "normale", "difficile"], type_list=["type1", "type2", "type3"]):
        self.difficulty = difficulty
        self.type_list = type_list

    def _select_diff(self):
        """ Permette all'utente di selezionare la difficoltà tra diverse opzioni.

        Restituisce la stringa diff_choice """

        while True:
            self.diff_choice = input(f"Scegli la difficoltà: {self.difficulty[0]}, {self.difficulty[1]} o {self.difficulty[2]}: ").lower()
            if self.diff_choice in self.difficulty:
                print(f"Hai scelto la difficoltà {self.diff_choice}\nGiochiamo!\n")
                return self.diff_choice
            else:
                print("\nHai inserito un valore di difficoltà non valido, riprova")

    def _switch_diff(self) -> int:
        """ Cambia il numero di domande nel gioco in base alla difficoltà 
        selezionata tramite select_diff.

        Restituisce il numero di domande n_questions """

        if self.diff_choice == self.difficulty[0]:
            self.n_questions = 3
        elif self.diff_choice == self.difficulty[1]:
            self.n_questions = 4
        elif self.diff_choice == self.difficulty[2]:
            self.n_questions = 5
        return self.n_questions
    
    def _diff_type1(self) -> int:
        """ Modifica le risposte delle domande di tipologia 1 in base alla 
        difficoltà selezionata.

        Restituisce "delta_inf" che cambierà l'intervallo in cui verranno generate
        le possibili risposte """

        if self.diff_choice == self.difficulty[0]:
            self.delta_inf = 20
        elif self.diff_choice == self.difficulty[1]:
            self.delta_inf = 10            
        elif self.diff_choice == self.difficulty[2]:
            self.delta_inf = 5
        return self.delta_inf

class Question:
    def __init__(self, score=0, correct=False):
        self.ia = Cinemagoer()
        self.score = score
        self.correct = correct
        self.pool = []
        self.type = None
        self.movie_year = None
        self.movie_title = None
        self.directors = []
        self.mp_string = ""
        self.answer_pool = []
        self.answer_dic = {}

    def _extract_pool(self) -> list:
        """ Definisce il "seed" della domanda estraendo una lettera casuale 
        che verrà usata per creare una pool di film. Se dopo tre tentativi 
        non è stato possibile connettersi al server, il gioco si ferma. 

        Restituisce la pool (pool) """

        letter = random.choice(string.ascii_letters)
        try:
            self.pool = [Movie for Movie in self.ia.search_movie(letter) if Movie['kind'] == 'movie']
            if len(self.pool) > 3:
                return self.pool
            else: 
                raise IMDbError
        except IMDbError:
            i = 0
            while i < 2:
                print("\n!!! Si è verificato un errore di connessione, per piacere attendere !!!\n")
                try:
                    self.pool = [Movie for Movie in self.ia.search_movie(letter) if Movie['kind'] == 'movie']
                    if len(self.pool) > 3:
                        return self.pool
                    else:
                        raise IMDbError
                except IMDbError:
                    time.sleep(10)
                i += 1
            print("\n\nOps! Qualcosa è andato storto, è necessario riavviare il gioco.")
        sys.exit(1)        

   
    def _question_type(self, config: Config) -> str:
        """ Seleziona casualmente la tipologia della domanda tra quelle 
        disponibili nella classe Config.

        Restituisce la tipologia (type) estratta """

        self.type = random.choice(config.type_list)
        return self.type
    
    
    def _correct_answer(self):
        """ Estrae casualmente dalla pool il film su cui si baserà la domanda e tutte le sue informazioni.

        Restituisce anno (movie_year), titolo (movie_title), trama (mp_string) e registi (directors) del film selezionato
        """

        self.index = random.randint(0, len(self.pool) - 1)
        chosen_movie = self.ia.get_movie(self.pool[self.index].movieID)
        self.movie_year = chosen_movie.get('year')
        self.movie_title = chosen_movie.get('title')
        self.directors = [director['name'] for director in chosen_movie.get('directors')]
        mp = chosen_movie.get('plot')
        self.mp_string = mp[0]
        del self.pool[self.index]
        return self.movie_year, self.movie_title, self.pool, self.mp_string, self.directors


    def _wrong_pool(self, config: Config) -> list:
        """ In base alla tipologia di domanda estratta in question_type, viene selezionata
        la risposta giusta e vengono definite le risposte sbagliate alle domande, costruendo una pool 
        con tutte le quattro risposte.

        Restituisce la pool (answer_pool) delle risposte tra cui il giocatore potrà scegliere
        """

        # Domanda Tipo 1
        if self.type == "type1":
            delta_inf = config._diff_type1()
            current_year = datetime.now().year
            delta_sup = delta_inf if (current_year - self.movie_year > delta_inf) else current_year - self.movie_year
            self.answer_pool = [self.movie_year]
            while len(self.answer_pool) < 4:
                i = random.randint(self.movie_year - delta_inf, self.movie_year + delta_sup)
                if i not in self.answer_pool:
                    self.answer_pool.append(i)
        # Domanda Tipo 2
        elif self.type == "type2":
            self.answer_pool = [self.movie_title]
            while len(self.answer_pool) < 4:
                self.index = random.randint(0, len(self.pool) - 1)
                wrong_movie = self.ia.get_movie(self.pool[self.index].movieID)
                wrong_title = wrong_movie.get("title")
                if wrong_title not in self.answer_pool:
                    self.answer_pool.append(wrong_title)
                    del self.pool[self.index]
        # Domanda Tipo 3
        else:
            self.answer_pool = [self.directors]
            while len(self.answer_pool) < 4:
                self.index = random.randint(0, len(self.pool) - 1)
                wrong_movie = self.ia.get_movie(self.pool[self.index].movieID)
                wrong_directors = [director['name'] for director in wrong_movie.get('directors', [])]
                if wrong_directors not in self.answer_pool:
                    self.answer_pool.append(wrong_directors)
                    del self.pool[self.index]
        return self.answer_pool

    
    def _answer_dictionary(self) -> dict:
        """ Associa ogni risposta dell'answer_pool a una lettera, in modo da 
        facilitare l'inserimento in input della risposta da parte dell'utente.

        Restituisce il dizionario (answer_dic) dove la lettera costituisce la chiave 
        e la risposta il valore"""

        key = ['A', 'B', 'C', 'D']
        random.shuffle(self.answer_pool)
        self.answer_dic = {key[i]: self.answer_pool[i] for i in range(len(self.answer_pool))}
        return self.answer_dic


    def _game_interface(self):
        """ Stampa a schermo la domanda e il dizionario con le possibili risposte. """

        if self.type == "type1":
            print(f">> In che anno è uscito {self.movie_title}?\n")
            print(f"Puoi scegliere tra una delle seguenti soluzioni:")
            for key, value in self.answer_dic.items():
                print(f"   {key}) {value}")
        elif self.type == "type2":
            print(">> Di che film sto parlando?\n")
            self.movie_plot = textwrap.fill(self.mp_string, width=70)
            print(f"{self.movie_plot}\n")
            print(f"Puoi scegliere tra una delle seguenti soluzioni:")
            for key, value in self.answer_dic.items():
                print(f"   {key}) {value}")
        else:
            print(f">> Chi è il regista di {self.movie_title}? \n")
            print(f"Puoi scegliere tra una delle seguenti soluzioni:")
            for key, value in self.answer_dic.items():
                print(f"   {key}) {', '.join(value)}")

    
    def _user_input(self):
        """ Chiede all'utente di selezionare la risposta inserendo in input la lettera 
        corrispondente, confronta la risposta data con la risposta corretta """

        while True:
            user_answer = input("Scegli la risposta digitando A, B, C oppure D: ").upper()
            if user_answer in ["A", "B", "C", "D"]:
                break
            else:
                print("\nHai inserito un valore scorretto, rispondi nuovamente")

        key_found = None
        for key, value in self.answer_dic.items():
            if self.type == "type1" and value == self.movie_year:
                key_found = key
            elif self.type == "type2" and value == self.movie_title:
                key_found = key
            elif self.type == "type3" and value == self.directors:
                key_found = key

        if user_answer == key_found:
            print("\nHai risposto correttamente!\n      -----------------\n")
            self.correct = True
        else:
            correct_answer = self.movie_title if self.type == "type2" else self.movie_year if self.type == "type1" else self.directors
            if self.type == "type3":
                print(f"\nHai sbagliato!\nLa risposta corretta è: '{', '.join(correct_answer)}'\n      ----------------- \n")
            else:
                print(f"\nHai sbagliato!\nLa risposta corretta è: '{correct_answer}'\n      ----------------- \n")
        return self.correct

class GameFlow:
    def __init__(self):
        self.score = 0
        self.diff_choice = None

    
    def _whole_question(self, question: Question, config: Config):
        """ Viene assemblata la domanda usando i metodi della classe Question.
        """

        q = question()
        q._question_type(Config())
        q._extract_pool()
        q._correct_answer()
        q._wrong_pool(config)
        q._answer_dictionary()
        q._game_interface()
        return q._user_input()

    def start_game(self, config: Config):
        """ Inizia il gioco, assegna il punteggio in base alla difficoltà selezionata e 
        lo stampa a schermo una volta che il gioco è finito """

        config = Config()  
        config._select_diff()     
        n_questions = config._switch_diff() 

        for _ in range(n_questions):
            correct = self._whole_question(Question, config)  
            if correct and config.diff_choice == config.difficulty[0]:
                self.score += 1 
            elif correct:
                self.score += 2 if config.diff_choice == config.difficulty[1] else 3

        print(f"Hai risposto a tutte le domande\nIl tuo punteggio finale è: {self.score}")

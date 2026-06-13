import fitparse

# Ścieżka relatywna zapewnia przenośność skryptu między środowiskami
file_path = r"Trening.fit"


# Dekoduje binarny plik FIT i wypisuje jego pełną zawartość na ekranie
def wyswietl_wszystko(file_path: str) -> None:

    # Implementuje bezpieczną obsługę błędów wejścia/wyjścia (I/O)
    # zgodnie z zasadami programowania defensywnego
    try:

        # Deserializacja binarnego formatu FIT do obiektów Pythona
        fit_file = fitparse.FitFile(file_path)

        for msg_idx, message in enumerate(fit_file.get_messages()):

            # Wypisanie numer indeksu, jego zawartości oraz identyfikatora wiadomości z nagłówka (jeśli istnieje)
            print(
                f"[KOMUNIKAT #{msg_idx}] TYP: {message.name.upper()} (ID: {message.header.local_mesg_num if hasattr(message, 'header') else 'brak'})"
            )

            # Iteracja po polach (FieldData) pojedynczej instancji klasy FitMessage
            for data in message:

                jednostka = f"{data.units}" if data.units else ""
                # Wypisuje atrybuty obiektu - nazwę, wartość oraz jednostkę (jeśli istnieje)
                print(f"{data.name}: {data.value}{jednostka}")
        print("-" * 50)
    except FileNotFoundError:

        print(f"[BŁĄD I/O]: Plik '{file_path}' nie istnieje w podanej ścieżce.")

    except PermissionError:

        print(
            f"[BŁĄD SYSTEMOWY]: Brak uprawnień do odczytu pliku '{file_path}'. "
            "Upewnij się, że plik nie jest zablokowany przez inny proces. "
        )

    except fitparse.FitParseError as error:
        print(f"[BŁĄD PARSOWANIA]: Plik FIT jest uszkodzony: {error}")

    except Exception as error:

        print(
            f"[BŁĄD KRYTYCZNY]: Nieoczekiwany wyjątek podczas przetwarzania danych: {error}"
        )

if __name__ == "__main__":
    # Punkt wejścia zapobiega automatycznemu uruchomieniu logiki przy importowaniu modułu
    wyswietl_wszystko(file_path)

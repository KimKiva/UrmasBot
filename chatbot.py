import random
import json
import pickle
import requests
import datetime
import numpy as np
import tensorflow as tf
import urllib.parse 

import nltk
from nltk.stem import WordNetLemmatizer
nltk.download('punkt')
nltk.download('wordnet')

import tkinter as tk
from tkinter import Scrollbar, Text
from tkinter import Label, PhotoImage

lemmatizer = WordNetLemmatizer()
intents = json.loads(open('intents_fi.json', encoding='utf-8').read())

words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))
model = tf.keras.models.load_model('chatbot_model_fi.h5')


def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word) for word in sentence_words] 
    return sentence_words


def bag_of_words(sentence):
    sentence_words = clean_up_sentence(sentence)
    bag = [0] * len(words)
    for w in sentence_words:
        for i, word in enumerate(words):
            if word == w:
                bag[i] = 1
    return np.array(bag)


def predict_class(sentence):
    bow = bag_of_words(sentence)
    
    if not any(word in words for word in sentence.split()):
        return [{'intent': 'error', 'probability': '1.0'}]
    
    res = model.predict(np.array([bow]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]
    
    results.sort(key=lambda x: x[1], reverse=True)
    if results:
        return_list = []
        for r in results:
            return_list.append({'intent': classes[r[0]], 'probability': str(r[1])})
        return return_list
    else:
        return None  


print("Botti on käynnissä")


class ChatInterface:
    
    def __init__(self, master):
        self.master = master
        master.title(" UrmasChatBot")
        master.geometry("550x550")
        master.resizable(False, False)

        self.chat_text = Text(master, state=tk.DISABLED, wrap=tk.WORD, width=48, height=20, font=("Roboto", 14), background="light gray") 
        self.scrollbar = Scrollbar(master, command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=self.scrollbar.set)

        self.input_entry = tk.Entry(master, width=50)
        self.send_button = tk.Button(master, text="Lähetä", command=self.send_message)

        self.chat_text.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.input_entry.grid(row=1, column=0)
        self.send_button.grid(row=2, column=0)


        self.master.grid_rowconfigure(1, weight=1) 
        self.master.grid_columnconfigure(1, weight=1)  
        
        
        self.image_frame = tk.Frame(master)
        self.image_frame.grid(row=3, column=0, columnspan=2)  
        
        self.teletext_image = None  
        
        self.input_entry.bind("<Return>", self.send_message)
        
        self.send_button.configure(width=15, justify="center")
        

        self.game_active = False
        self.bot_number = 0
        self.attempts = 0
        self.last_user_input = "" 
        
        self.instruction_index = 0
        self.instructions = [
            'Tervetuloa käyttämään UrmasBotin versiota 0.45. Tässä versiossa uutena toimintona tulee\nteksti-tv:n, laskutoimituksien ja tiedonhaun lisäksi kyky hakea AO-Spesian Järvenpään toimipaikan päivän ruokalista. Jos haluat lisäohjeita botin käyttöön, kirjoita chattiin "ohjeet".',
            'Jos haluat viimeisimpiä uutisotsikoita suomesta, kirjoita chattiin esim. "näytä teksti-tv", "saisinko uutiset" tai "mitä tänään on uutisissa". Teksti-tv toiminnon lähde on Yle.',
            'Jos haluat nähdä teksti-tv:n uutisia, kirjoita chattiin esim. "näytä teksti-tv", "saisinko uutiset" tai "mitä tänään on uutisissa". Teksti-tv toiminnon lähde on Yle.',
            'Voit laskea erilaisia laskutoimituksia, kuten yhteenlaskuja, vähennyslaskuja, kertolaskuja ja jakolaskuja. Voit kirjoittaa esimerkiksi "Laske 5 kertaa 2 " ja "10 jaettuna 2" tai muodossa "5*2", "10/2" jne.',
            'Jos haluat pelata numeronarvauspeliä, kirjoita chattiin "pelaa".',
            'Jos haluat tietoa jostakin aiheesta, kirjoita chattiin esim. "kerro tietoa aiheesta jalkapallo" tai "hae tietoa henkilöstä tarja halonen". Urmas yrittää hakea tietoa Wikipedia-sivustolta valitsemastasi aiheesta.',
            'Jos haluat jonkin paikkakunnan sään, kirjoita chattiin esim. "sää helsinki".',
            'Jos haluat Järvenpään Spesian päivän ruokalistan, kirjoita chattiin esim "hae ruokalista" tai "kerro päivän ruoka".',
            'Hauskaa chattailyä :).'
            ]
        
      
        self.display_first_instruction() 

    
    def get_responses(self, intents_list, intents_json):
        tag = intents_list[0]['intent']
        print("Intent Tag:", tag)
        list_of_intents = intents_json['intents']

        for i in list_of_intents:
            if i['tag'] == tag:
                result = random.choice(i['responses'])
                return result  
   
        if tag == 'tiedonhaku':
            self.process_wikipedia_input(self.last_user_input)  # Use the last_user_input attribute of the instance

        # Return the default response only if no matching tag is found
        return "Anteeksi, en ymmärrä syötettä."
    
    def display_first_instruction(self):
        instruction = self.instructions[0]  
        self.update_chat(f'\nUrmas: {instruction}')

    
    
    def display_instructions(self):
        if self.instruction_index < len(self.instructions):
            instruction = self.instructions[self.instruction_index]
            self.update_chat(f'\nUrmas: {instruction}')
            self.instruction_index += 1
            self.master.after(7000, self.display_instructions)
                 
                 
    def send_message(self, event=None):
        message = self.input_entry.get()
        self.input_entry.delete(0, tk.END)

        if message.strip():
            self.update_chat("\nSinä: " + message)

            if self.game_active:
                self.process_game_input(message)
            else:
                self.process_user_input(message)
            
            # Remove the image label from the frame when a new message is sent
            if hasattr(self, "image_label"):
                self.image_label.destroy()
        else:
            self.input_entry.delete(0, tk.END)
                
            
    def extract_city(self, user_input):
        keywords = ["sää", "kaupunki", "kaupungissa"]
        for keyword in keywords:
            if keyword in user_input.lower():
                words = user_input.lower().split()
                city_index = words.index(keyword) + 1
                if city_index < len(words):
                    return words[city_index]
        return 
    
    
    def get_weather(self, city):
        api_key = "ca87ffa7b18dd5542a008cb9330ddac4"

        base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=fi"
        response = requests.get(base_url)
        data = response.json()

        print("API Response:", data)
        
        city_capital = city.capitalize()
        

        if data["cod"] == 200:
            weather_description = data["weather"][0]["description"]
            temperature = data["main"]["temp"]
            
        if "main" in data and "temp" in data["main"]:
            temperature = data["main"]["temp"]
            temperature_rounded = round(temperature)
            return f"Sää paikkakunnalla {city_capital}: {weather_description}, lämpötila {temperature_rounded}°C"
        else:
            return "Sään hakeminen epäonnistui. Tarkista kaupungin nimi ja yritä uudelleen."
            
            
    def process_game_input(self, user_input):
        if user_input.isdigit():
            user_guess = int(user_input)
            self.check_game_guess(user_guess)
        else:
            self.update_chat("\nUrmas: Anna vain numeroina.")


    def check_game_guess(self, user_guess):
        if user_guess == 0:
            self.end_game()
        elif user_guess < self.bot_number:
            self.update_chat("\nUrmas: Liian pieni! Yritä uudelleen.")
            self.attempts+=1
        elif user_guess > self.bot_number:
            self.update_chat("\nUrmas: Liian suuri! Yritä uudelleen.")
            self.attempts+=1
        else:
            self.update_chat(f"\nUrmas: Oikein! Arvasit numeron {self.attempts} yrityksellä.")
            self.attempts+=1
            self.end_game()


    def start_number_guessing_game(self):
        self.bot_number = random.randint(1, 1000)
        self.attempts = 0
        self.update_chat("\nUrmas: Botti on valinnut numeron väliltä 1-1000. Arvaa mikä se on! 0 Lopettaa pelin.")
        self.game_active = True


    def end_game(self):
        self.update_chat("\nUrmas: Peli päättyi. Voit jatkaa keskustelua.")
        self.game_active = False

    
    def process_percentage_input(self, user_input):
        if "prosenttia luvusta" in user_input.lower():
            try:
                parts = user_input.split()
                percent_index = parts.index("prosenttia")
                number_index = parts.index("luvusta")
                number = float(parts[number_index + 1])
                result = number * (float(parts[percent_index - 1]) / 100)
                return f"{result:.2f}"
            except Exception as e:
                return None
        return None


    def process_multiply_input(self, user_input):
        if "kertaa" in user_input.lower():
            try:
                parts = user_input.split()
                multiply_index = parts.index("kertaa")
                number1 = float(parts[multiply_index - 1])
                number2 = float(parts[multiply_index + 1])
                result = number1 * number2
                return f"{round(result)}"
            except Exception as e:
                return "Virhe laskussa. Tarkista syöte."
        return None


    def process_addition_input(self, user_input):
        if "plus" in user_input.lower():
            try:
                parts = user_input.split()
                multiply_index = parts.index("plus")
                number1 = float(parts[multiply_index - 1])
                number2 = float(parts[multiply_index + 1])
                result = number1 + number2
                return f"{round(result)}"
            except Exception as e:
                return "Virhe laskussa. Tarkista syöte."
        return None
    
    def process_subtraction_input(self, user_input):
        if "miinus" in user_input.lower():
            try:
                parts = user_input.split()
                multiply_index = parts.index("miinus")
                number1 = float(parts[multiply_index - 1])
                number2 = float(parts[multiply_index + 1])
                result = number1 - number2
                return f"{round(result)}"
            except Exception as e:
                return "Virhe laskussa. Tarkista syöte."
        return None
    
    def process_divide_input(self, user_input):
        if "jaettuna" in user_input.lower():
            try:
                parts = user_input.split()
                multiply_index = parts.index("jaettuna")
                number1 = float(parts[multiply_index - 1])
                number2 = float(parts[multiply_index + 1])
                result = number1 / number2
                return f"{result:.2f}"
            except Exception as e:
                return "Virhe laskussa. Tarkista syöte."
        return None
    
    
    def process_modulo_input(self, user_input):
        if "modulo" in user_input.lower() or "jakojäännös" in user_input.lower():
            try:
                parts = user_input.split()
                modulo_index = parts.index("modulo") if "modulo" in parts else parts.index("jakojäännös")
                number1 = float(parts[modulo_index - 1])
                number2 = float(parts[modulo_index + 1])
                result = number1 % number2
                return f"{result:.0f}"
            except Exception as e:
                return "Virhe laskussa. Tarkista syöte."
        return None
    
    
    def get_wikipedia_info(self, title):
        encoded_title = urllib.parse.quote(title, safe='')  # Use safe='' to allow underscores
        base_url = f"https://fi.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
        response = requests.get(base_url)
        
        return response.json()  # Return the entire JSON response


    def process_wikipedia_input(self, user_input):
        try:
            lower_input = user_input.lower()
            excluded_words = ["aiheesta", "henkilöstä", "paikasta", "asiasta", "ohjelmistosta", "sovelluksesta", "hae", "kerro"]
            if "tietoa" in lower_input:
                topic = user_input.lower().replace("tietoa", "").strip()
                formatted_topic = "_".join(word.capitalize() for word in topic.split() if word not in excluded_words)
                print("Debug: Transformed topic:", formatted_topic)
                
                wikipedia_info = self.get_wikipedia_info(formatted_topic)
                print("Debug: Retrieved Wikipedia info:", wikipedia_info)
                self.update_chat("\nUrmas: " + wikipedia_info.get("extract", "Anteeksi, en löytänyt tietoja kyseisestä aiheesta."))
        except:
            self.update_chat("\nUrmas: Anteeksi, en ymmärrä pyyntöäsi.")
    
    
    def fetch_and_display_teletext_image(self, page_number, subpage_number):
        app_id = "551e3769"
        app_key = "bf51a8bae95232b6d4b1a6d608f7ec86"
        image_url = f"https://external.api.yle.fi/v1/teletext/images/{page_number}/{subpage_number}.png?app_id={app_id}&app_key={app_key}"
  
        response = requests.get(image_url)
        print("Response Status Code:", response.status_code)
        print("Response Content Length:", len(response.content))

        if response.status_code == 200:
            image_data = response.content
            teletext_image = PhotoImage(data=image_data)
            self.display_image_window(teletext_image)
        else:
            print("Error fetching teletext image.")
  
  
    def display_image_window(self, image):
        image_window = tk.Toplevel(self.master)
        image_window.resizable(False, False)
        image_label = Label(image_window, image=image)
        image_label.image = image
        image_label.pack()
    
    
    def get_daily_menu(self, target_date):
        target_date_num = int(target_date)
        url = "https://fi.jamix.cloud/apps/menuservice/rest/haku/menu/98304/24?lang=fi"
        response = requests.get(url)

        if response.status_code == 200:
            menu_data = response.json()

            for menu_type in menu_data[0]['menuTypes']:
                for menu in menu_type['menus']:
                    for day_data in menu['days']:
                        if day_data['date'] == target_date_num:
                            # day_name = self.get_day_name(day_data['weekday'])
                            daily_menu = ""

                            for meal_option in day_data['mealoptions']:
                                for menu_item in meal_option['menuItems']:
                                    food_name = menu_item['name']
                                    daily_menu += f"- {food_name}\n"

                            return f"\n{daily_menu}"

            return "Päivän ruokalistaa ei löytynyt"

        return "Ruokalistan hakeminen epäonnistui"


    def get_day_name(self, weekday_number):
        weekdays = ["maanantai", "tiistai", "keskiviikko", "torstai", "perjantai", "lauantai", "sunnuntai"]
        return weekdays[weekday_number - 1] if 1 <= weekday_number <=  7 else "Tuntematon päivä"

 
    def process_user_input(self, user_input):
        print("Debug: Käsitellään käyttäjän syötettä:", user_input)
        
       
        if any(keyword in user_input.lower() for keyword in ["pelaa numeronarvauspeliä", "pelaa", "pelataanko"]):
            self.start_number_guessing_game()
        
        elif 'ohjeet' in user_input.lower():
            self.instruction_index = 0  # Reset instruction index
            self.display_instructions()  # Start displaying instructions
        
        elif any(keyword in user_input.lower() for keyword in ["hae ruokalista", "kerro päivän ruoka", "mitä on ruokaa tänään on"]):
            current_day_number = datetime.datetime.now().strftime("%Y%m%d")
            current_day_for_user = datetime.datetime.now().strftime("%d.%m.%Y")
            daily_menu = self.get_daily_menu(current_day_number)  
            self.update_chat(f"\nUrmas: Tässä Järvenpään spesian ruokalista {current_day_for_user}:\n{daily_menu}")
        
        elif "sää" in user_input.lower():
            print("Debug: Käsitellään säähän liittyvää kysymystä")
            city = self.extract_city(user_input)
            print("Debug: Kaupunki:", city)
            if city:
                weather_response = self.get_weather(city)
                print("Debug: Säävastaus:", weather_response)
                self.update_chat("\nUrmas: " + weather_response)
            else:
                self.update_chat("Urmas: Minkä kaupungin säätä haluat tietää?")
        
        elif "tietoa" in user_input:
            self.process_wikipedia_input(user_input)

        elif any(keyword in user_input.lower() for keyword in ["uutiset", "uutisia", "teksti-tv", "uutisissa"]):
            self.update_chat(f"\nUrmas: Tässä ole hyvä :)")
            self.fetch_and_display_teletext_image("100", "1")  # Replace with the appropriate page and subpage numbers
            return  # Return after displaying the image, so no further processing is done

        elif any(keyword in user_input for keyword in ["+", "-", "*", "/"]):
            try:
                result = eval(user_input)
                self.update_chat(f"\nUrmas: Laskutoimituksen tulos: {result}")
            except Exception as e:
                self.update_chat("\nUrmas: Virhe laskutoimituksessa. Tarkista syöte.")

        elif any(keyword in user_input for keyword in ["prosenttia"]):
            result = self.process_percentage_input(user_input)
            if result:
                self.update_chat(f"\nUrmas: Laskutoimituksen tulos: {result}")
            else:
                self.update_chat("\nUrmas: Virhe prosenttilaskutoimituksessa. Tarkista syöte.")
                
        elif any(keyword in user_input for keyword in ["kertaa"]):
            result = self.process_multiply_input(user_input)
            if result:
                self.update_chat(f"\nUrmas: Laskutoimituksen tulos: {result}")
            else:
                self.update_chat("\nUrmas: Virhe laskutoimituksessa. Tarkista syöte.")
                
        elif any(keyword in user_input for keyword in ["plus"]):
            result = self.process_addition_input(user_input)
            if result:
                self.update_chat(f"\nUrmas: Laskutoimituksen tulos: {result}")
            else:
                self.update_chat("\nUrmas: Virhe laskutoimituksessa. Tarkista syöte.")
                
        elif any(keyword in user_input for keyword in ["miinus"]):
            result = self.process_subtraction_input(user_input)
            if result:
                self.update_chat(f"\nUrmas: Laskutoimituksen tulos: {result}")
            else:
                self.update_chat("\nUrmas: Virhe laskutoimituksessa. Tarkista syöte.")
                
        elif any(keyword in user_input for keyword in ["jaettuna"]):
            result = self.process_divide_input(user_input)
            if result:
                self.update_chat(f"\nUrmas: Laskutoimituksen tulos: {result}")
            else:
                self.update_chat("\nUrmas: Virhe laskutoimituksessa. Tarkista syöte.")
                
        elif any(keyword in user_input for keyword in ["modulo", "jakojäännös"]):
            result = self.process_modulo_input(user_input)
            if result:
                self.update_chat(f"\nUrmas: Laskutoimituksen tulos: {result}")
            else:
                self.update_chat("\nUrmas: Virhe laskutoimituksessa. Tarkista syöte.")

        else:
                ints = predict_class(user_input)
                if ints is not None:  
                    res = self.get_responses(ints, intents)
                    self.update_chat("\nUrmas: " + res)
                else:
                    self.update_chat("Urmas: Anteeksi, en ymmärrä mitä tarkoitat.")
                    
        
    def update_chat(self, message):
        self.chat_text.configure(state=tk.NORMAL)
        self.chat_text.insert(tk.END, message + "\n")
        self.chat_text.configure(state=tk.DISABLED)
        self.chat_text.see(tk.END)
                        
                
root = tk.Tk()
chat_interface = ChatInterface(root)
root.mainloop() 
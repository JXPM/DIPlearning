#Installer Kiwix-serve
sudo apt update
sudo apt install kiwix-tools -y


#version de wikipedia en francais
wget https://download.kiwix.org/zim/wikipedia_fr_all_maxi_2024-05.zim

#lancer le serveur
kiwix-serve --port=8080 wikipedia_fr_all_maxi_2024-05.zim

#acceder a la page
http://192.168.4.1:8080

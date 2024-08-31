Le projet se base sur le package open source **seahorse**. Vous pouvez le soutenir en déposant une étoile sur sa page github. 

### Installation
Pour lancer une partie, il faut donc au préalable installer **seahorse** à l’aide de la commande suivante :

```bash
$ pip install seahorse colorama
```

Ensuite, plusieurs modes d’exécution sont disponibles via la présence d’arguments. Par exemple, `-r` permet d’enregistrer une partie dans un fichier JSON. Pour obtenir la description de tous les arguments, exécutez la commande suivante :

```bash
$ python main_divercite.py -h
```

### Lancer une partie

Pour lancer une partie en local avec GUI, utilisez par exemple la commande suivante :

```bash
$ python main_divercite.py -t local random_player_divercite.py random_player_divercite.py
```

La commande suivante lance une partie en local entre l’agent aléatoire et l’agent glouton, les logs sont enregistrés dans un fichier JSON, mais la GUI n’est pas ouverte :

```bash
$ python main_divercite.py -t local random_player_divercite.py greedy_player_divercite.py -r -g
```

### Organiser une partie avec un autre groupe

Pour organiser une partie contre un agent d’un autre groupe, lancez la commande suivante pour héberger le match :

```bash
$ python main_divercite.py -t host_game -a <ip_address> random_player_divercite.py
```

L’équipe que vous souhaitez affronter devra lancer la commande suivante :

```bash
$ python main_divercite.py -t connect -a <ip_address> random_player_divercite.py
```

Remplacez `<ip_address>` par l’adresse IP de l’ordinateur qui héberge la partie. Pour obtenir cette dernière, exécutez la commande `ipconfig` (Windows) ou `ifconfig` (Mac, Linux) dans un terminal.

### Jouer manuellement

Il est possible de jouer manuellement l’un contre l’autre avec la commande suivante :

```bash
$ python main_divercite.py -t human_vs_human
```

Pour étudier le comportement de votre agent, vous pouvez jouer manuellement contre ce dernier avec :

```bash
$ python main_divercite.py -t human_vs_computer random_player_divercite.py
```

En cas de problèmes, n’hésitez pas à communiquer avec votre chargé de laboratoire à l’aide de **Slack**.

**Note :** Il est préférable de ne pas utiliser le navigateur **Safari** pour afficher l’interface graphique.

**Conseil :** Assurez-vous que vous êtes capables de faire tourner le code du projet au plus tôt.

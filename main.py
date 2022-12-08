import bot.bot as bot

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser
configpath = "config.cfg"

if __name__ == '__main__':
    config = ConfigParser()
    config.read(configpath)
    TOKEN = config.get('Kugane Fisher', 'discord_token')
    bot.run(TOKEN)


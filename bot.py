import asyncio
import ssl
import yaml
from flask_socketio import SocketIO

socketio = SocketIO(message_queue='redis://')

class IRCBot:
    def __init__(self, config):
        self.config = config
        self.reader = None
        self.writer = None
        self.connected = False

    async def connect(self):
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH) if self.config['use_ssl'] else None
        self.reader, self.writer = await asyncio.open_connection(self.config['server'], self.config['port'], ssl=ssl_context)
        if 'password' in self.config:
            self.send_raw(f"PASS {self.config['password']}")
        self.send_raw(f"NICK {self.config['nickname']}")
        self.send_raw(f"USER {self.config['nickname']} 0 * :{self.config['realname']}")

    def send_raw(self, message):
        print(f"Sending: {message}")
        self.writer.write((message + '\r\n').encode())

    async def handle_messages(self):
        while True:
            line = await self.reader.readline()
            if not line:
                break
            line = line.decode().strip()
            words = line.split()
            if line.startswith('PING'):
                self.send_raw('PONG ' + words[1])
            elif len(words) >= 2 and words[1] == '001' and not self.connected:
                self.send_raw(f"JOIN {self.config['channel']}")
                self.connected = True
            socketio.emit('message', {'data': line})
            print(line)

    async def run(self):
        await self.connect()
        await self.handle_messages()

def main():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    bot = IRCBot(config)
    asyncio.run(bot.run())

if __name__ == "__main__":
    main()

#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    logged_on_cli = []
    history = []
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):

        decoded = data.decode()

        if self.login in self.logged_on_cli:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                self.login = decoded.replace("login:", "").replace("\r\n", "").strip()
                if self.login in self.logged_on_cli:
                    self.transport.write(
                        f"Пользователь {self.login} занят\r\n".encode()
                    )
                    self.login = None
                elif len(self.login) < 3:
                    self.transport.write(
                        f"Имя пользователя должно быть >= 3 символов\r\n".encode()
                    )
                    self.login = None
                else:
                    self.transport.write(
                        f"Привет, {self.login}!\r\n".encode()
                    )
                    self.send_history()
                    self.logged_on_cli.append(self.login)
            else:
                self.transport.write("Введите команду login: \"имя мользователя\" для регистрации\r\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print(f"Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        self.logged_on_cli.remove(self.login)
        print(f"Клиент вышел {self.login}")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\r\n"

        if len(self.history) <= 10:
            self.history.append(message)
        else:
            del self.history[0]
            self.history.append(message)

        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self):
        for message in self.history:
            self.transport.write(
                message.encode()
            )


class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")

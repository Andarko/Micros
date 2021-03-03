#!/usr/bin/env python
# import aiohttp.web_server as web
import asyncio
import logging
import websockets
import json
import time
import RPi.GPIO as GPIO
from websockets import WebSocketServerProtocol

logging.basicConfig(level=logging.INFO)


class Server:
    clients = set()

    def __init__(self):
        self.status = "uninitialized"

        self.coord = [-1, -1, -1]
        # self.coordX = -1
        # self.coordY = -1
        # self.coordZ = -1

        limits_mm = [340, 630, 90]
        steps_in_mm = 80
        self.limits = []
        for lim in limits_mm:
            self.limits.append(lim * steps_in_mm)
        # self.limitX = 340 * 80
        # self.limitY = 630 * 80
        # self.limitZ = 90 * 80

        self.max_count_signals = 80

        self.STEP_PLUS = [7, 15, 29]
        self.STEP_MINUS = [8, 16, 31]
        self.DIR_PLUS = [10, 18, 32]
        self.DIR_MINUS = [11, 19, 33]
        self.ENB_PLUS = [12, 21, 35]
        self.ENB_MINUS = [13, 22, 36]

        self.SENSOR = [23, 24, 26]

        self.delay = 100 / 1000 / 1000

        # print("init success")

    async def register(self, ws: WebSocketServerProtocol) -> None:
        self.clients.add(ws)
        # logging.info(f'{ws.remote_address} connects.')

    async def unregister(self, ws: WebSocketServerProtocol) -> None:
        self.clients.remove(ws)
        # logging.info(f'{ws.remote_address} disconnects.')

    async def send_to_clients(self, message: str) -> None:
        if self.clients:
            await asyncio.wait([client.send(message) for client in self.clients])

    async def ws_handler(self, ws: WebSocketServerProtocol, url: str) -> None:
        await self.register(ws)
        try:
            await self.distribute(ws)
        finally:
            await self.unregister(ws)

    async def distribute(self, ws: WebSocketServerProtocol) -> None:
        async for message in ws:
            request = json.loads(message)
            if request["mode"] == "init":
                response = await self.init()
                await self.send_to_clients(response)
            elif request["mode"] == "discrete":
                response = await self.move_xyz(request)
                await self.send_to_clients(response)
            elif request["mode"] == "check":
                response = await self.check()
                await self.send_to_clients(response)
            else:
                response = await self.move_xyz(request)
                await self.send_to_clients(response)

    @staticmethod
    async def get_dir(dist):
        if dist < 0:
            direction = "b"
        else:
            direction = "f"
        return direction

    async def init_move(self, dist):
        directions = [await self.get_dir(dist[0]), await self.get_dir(dist[1]), await self.get_dir(dist[2])]
        distances = [abs(dist[0]) * 2, abs(dist[1]) * 2, abs(dist[2]) * 2]
        GPIO.setmode(GPIO.BOARD)
        for i in range(3):
            GPIO.setup(self.STEP_PLUS[i], GPIO.OUT)
            GPIO.setup(self.STEP_MINUS[i], GPIO.OUT)
            GPIO.setup(self.DIR_PLUS[i], GPIO.OUT)
            GPIO.setup(self.DIR_MINUS[i], GPIO.OUT)
            GPIO.setup(self.ENB_PLUS[i], GPIO.OUT)
            GPIO.setup(self.ENB_MINUS[i], GPIO.OUT)
            GPIO.setup(self.SENSOR[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # noinspection PyBroadException
        try:
            for i in range(3):
                GPIO.output(self.ENB_MINUS[i], GPIO.LOW)
                GPIO.output(self.STEP_MINUS[i], GPIO.LOW)
                GPIO.output(self.DIR_MINUS[i], GPIO.LOW)

            GPIO.output(self.ENB_PLUS, GPIO.LOW)

            if directions[0] == "b":
                GPIO.output(self.DIR_PLUS[0], GPIO.LOW)
            elif directions[0] == "f":
                GPIO.output(self.DIR_PLUS[0], GPIO.HIGH)
            if directions[1] == "f":
                GPIO.output(self.DIR_PLUS[1], GPIO.LOW)
            elif directions[1] == "b":
                GPIO.output(self.DIR_PLUS[1], GPIO.HIGH)
            if directions[2] == "f":
                GPIO.output(self.DIR_PLUS[2], GPIO.LOW)
            elif directions[2] == "b":
                GPIO.output(self.DIR_PLUS[2], GPIO.HIGH)

            # delay = 50 / 1000 / 1000
            count_of_signals = [0, 0, 0]
            steps = distances
            max_steps = max(steps)
            # print(max_steps)
            breaking = False
            for i in range(max_steps):
                # включаем сигнал step по тем осям, которые надо двигать
                for j in range(3):
                    if steps[j] > 0:
                        GPIO.output(self.STEP_PLUS[j], GPIO.HIGH)
                time.sleep(self.delay)
                for j in range(3):
                    if steps[j] > 0:
                        GPIO.output(self.STEP_PLUS[j], GPIO.LOW)
                        steps[j] -= 1
                        if directions[j] == "b":
                            signal = GPIO.input(self.SENSOR[j])
                            if count_of_signals[j] < self.max_count_signals:
                                if signal == 0:
                                    count_of_signals[j] += 1
                                else:
                                    count_of_signals[j] = 0
                            else:
                                print("end cap activate (axis {})".format(j))
                                steps[j] = 0
                                # print(steps)
                                if max(steps) == 0:
                                    breaking = True
                                    break
                time.sleep(self.delay)
                if breaking:
                    break
            print("finish init")
        except KeyboardInterrupt:
            print("Keyboard interrupt")
        except Exception:
            print("some error")
        finally:
            print("clean up")
            GPIO.cleanup()

    async def move_xyz(self, json_obj):
        x = self.coord[0] + json_obj["x"]
        y = self.coord[1] + json_obj["y"]
        z = self.coord[2] + json_obj["z"]
        xyz = [x, y, z]

        if self.status == "error":
            err_response = await self.get_json(self.coord[0], self.coord[1], self.coord[2], "err_server")
            return err_response

        if self.status == "inited":
            if x < 0 or x > self.limits[0] or y < 0 or y > self.limits[1] or z < 0 or z > self.limits[2]:
                err_response = await self.get_json(self.coord[0], self.coord[1], self.coord[2], "err_coord")
                return err_response

        GPIO.setmode(GPIO.BOARD)

        for i in range(3):
            GPIO.setup(self.STEP_PLUS[i], GPIO.OUT)
            GPIO.setup(self.STEP_MINUS[i], GPIO.OUT)
            GPIO.setup(self.DIR_PLUS[i], GPIO.OUT)
            GPIO.setup(self.DIR_MINUS[i], GPIO.OUT)
            GPIO.setup(self.ENB_PLUS[i], GPIO.OUT)
            GPIO.setup(self.ENB_MINUS[i], GPIO.OUT)
            GPIO.setup(self.SENSOR[i], GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # noinspection PyBroadException
        try:
            for i in range(3):
                GPIO.output(self.ENB_MINUS[i], GPIO.LOW)
                GPIO.output(self.STEP_MINUS[i], GPIO.LOW)
                GPIO.output(self.DIR_MINUS[i], GPIO.LOW)

            GPIO.output(self.ENB_PLUS, GPIO.LOW)
            directions = [await self.get_dir(json_obj["x"]), await self.get_dir(json_obj["y"]),
                          await self.get_dir(json_obj["z"])]

            if directions[0] == "b":
                GPIO.output(self.DIR_PLUS[0], GPIO.LOW)
            elif directions[0] == "f":
                GPIO.output(self.DIR_PLUS[0], GPIO.HIGH)
            if directions[1] == "f":
                GPIO.output(self.DIR_PLUS[1], GPIO.LOW)
            elif directions[1] == "b":
                GPIO.output(self.DIR_PLUS[1], GPIO.HIGH)
            if directions[2] == "f":
                GPIO.output(self.DIR_PLUS[2], GPIO.LOW)
            elif directions[2] == "b":
                GPIO.output(self.DIR_PLUS[2], GPIO.HIGH)

            steps = [abs(json_obj["x"]) * 2, abs(json_obj["y"]) * 2, abs(json_obj["z"]) * 2]

            count_of_signals = [0, 0, 0]
            max_steps = max(steps)

            for i in range(max_steps):
                # включаем сигнал step по тем осям, которые надо двигать
                for j in range(3):
                    if steps[j] > 0:
                        GPIO.output(self.STEP_PLUS[j], GPIO.HIGH)
                time.sleep(self.delay)
                for j in range(3):
                    if steps[j] > 0:
                        GPIO.output(self.STEP_PLUS[j], GPIO.LOW)
                        steps[j] -= 1
                        if directions[j] == "b":
                            signal = GPIO.input(self.SENSOR[j])
                            if count_of_signals[j] < self.max_count_signals:
                                if signal == 0:
                                    count_of_signals[j] += 1
                                else:
                                    count_of_signals[j] = 0
                            else:
                                print("end cap activate (axis {})".format(j))
                                xyz[j] += int(steps[j] / 2)
                                steps[j] = 0
                time.sleep(self.delay)

        except KeyboardInterrupt:
            print("Keyboard interrupt")
        except Exception:
            print("some error")
        finally:
            print("clean up")
            GPIO.cleanup()

        self.coord[0] = xyz[0]
        self.coord[1] = xyz[1]
        self.coord[2] = xyz[2]
        response = await self.get_json(self.coord[0], self.coord[1], self.coord[2], self.status)
        return response
        # print("set GPIO high")

    @staticmethod
    async def check_pin(pin):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        signal = GPIO.input(pin)
        return signal

    async def init(self):
        # print("init!")
        for i in range(3):
            sensor = self.SENSOR[i]
            signals_count = 0
            for j in range(1000):
                signal = await self.check_pin(sensor)
                if signal == 0:
                    signals_count += 1
            if signals_count > 920:
                if i == 0:
                    # print("x first")
                    await self.init_move([500, 0, 0])
                elif i == 1:
                    # print("y first")
                    await self.init_move([0, 500, 0])
                else:
                    # print("z first")
                    await self.init_move([0, 0, 500])
            time.sleep(0.1)

        # print("x second")
        time.sleep(0.1)
        # print("y second")
        time.sleep(0.1)
        # print("z second")
        await self.init_move([-self.limits[0], -self.limits[1], -self.limits[2]])

        self.coord[0] = 0
        self.coord[1] = 0
        self.coord[2] = 0
        self.status = "inited"

        json_str = await self.get_json(self.coord[0], self.coord[1], self.coord[2], self.status)
        return json_str

    @staticmethod
    async def get_json(x, y, z, status):
        data = {
            "x": x,
            "y": y,
            "z": z,
            "status": status
        }
        json_str = json.dumps(data)
        return json_str

    async def check(self):
        data = {
            "x": self.coord[0],
            "y": self.coord[1],
            "z": self.coord[2],
            "status": self.status
        }
        json_str = json.dumps(data)
        return json_str


server = Server()
start_server = websockets.serve(server.ws_handler, '192.168.42.100', 8080)
loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.run_forever()

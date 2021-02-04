import asyncio
import websockets
import logging
import json

hostname="localhost"
port=5001


async def consumer(hostname:str ,port:int):
    url = f"ws://{hostname}:{port}"
    async with websockets.connect(url) as websocket:
        await hello(websocket)


async def hello(websocket)->None:
    async for message in websocket:
        print(message)


async def produce(message:str,host:str,port:int)->None:
    async with websockets.connect(f"ws://{host}:{port}")as ws:
        # for i in range(600):
        print("=> " + message)
        await ws.send(message)
        resp = await ws.recv()
        print("<= " + resp)
        return resp


def getrequest(xstep:int,ystep:int,zstep:int,mode:str):
    data = {
        "x": xstep,
        "y": ystep,
        "z": zstep,
        "mode": mode # continuous/discret/init/check
    }

    datastring = json.dumps(data)
    return datastring

# def moveSquare(loop,coordX,coordY,coordZ):
#     data1 = getrequest(xstep=0,ystep=0,zstep=0,mode="init")
#     response = loop.run_until_complete(produce(message=data1,host=hostname,port=port))

#     # data1 = getrequest(xstep=0,ystep=0,zstep=0,mode="init")
#     print(response,": response")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    data = getrequest(xstep=0,ystep=0,zstep=0,mode="init")
    # print(data)
    result = loop.run_until_complete(produce(message=data,host=hostname,port=port))
    # print(result)
    # moveSquare(loop,0,0,0)

    # loop.run_until_complete(consumer(hostname=hostname,port=port))
    loop.run_forever()

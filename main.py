import asyncio

from web3 import AsyncWeb3

from functions import *
from config import *
import chain_settings


async def producer(queue, private_key, number):
    await queue.put((private_key, number))
    print('\n', f'\033[31;47mPrivate key {private_key[:6]}...{private_key[-6:]} has been added to the queue. Queue №{number}\033[0m',
          '\n')


async def consumer(queue, color):
    while True:
        item = await queue.get()
        private_key, process_number = item

        timesleep_value = create_random_value_from_range(MIN_TIMESLEEP_BETWEEN_PROCESSES,
                                                         MAX_TIMESLEEP_BETWEEN_PROCESSES)

        print(f'{color} ▶️ Before the start of the process №{process_number} {timesleep_value} sec.', '\n')

        await asyncio.sleep(timesleep_value)

        try:
            for chain in map(chain_settings.__dict__.get, chain_settings.__all__):
                chain_name = chain['name']

                print(f'{color}Process №{process_number} has been launched for {private_key[:6]}...{private_key[-6:]} on the network {chain_name}')

                web3 = AsyncWeb3(AsyncWeb3.AsyncHTTPProvider(chain['url']))

                if not await web3.is_connected():
                    print(f'{color}Process №{process_number} connection to {chain_name} is not established', '\n')

                    my_address = web3.eth.account.from_key(private_key).address
                    await save_report_to_global_list(chain_name, my_address,
                                                     '-', 'ERROR',
                                                     '-', '-',
                                                     'Connection is not established')
                    await asyncio.sleep(5)
                    continue

                print(f'{color}Process №{process_number} connection to {chain_name} was established', '\n')

                transactions_quantity = create_random_value_from_range(chain['min_transactions'],
                                                                       chain['max_transactions'])

                for _ in range(transactions_quantity):
                    amount = create_random_amount_for_sending(chain['min_amount_for_sending'],
                                                              chain['max_amount_for_sending'],
                                                              NUMBER_OF_VARIATIONS_BETWEEN_SENDING_AMOUNT)

                    await random.choice([self_transaction, random_transaction])(web3, amount, private_key,
                                                                                MIN_TIMESLEEP_BETWEEN_TRANSACTIONS,
                                                                                MAX_TIMESLEEP_BETWEEN_TRANSACTIONS,
                                                                                chain_name, chain['explorer_url'],
                                                                                process_number, color)

            queue.task_done()

        except Exception as error:
            print(error, '\n')
            await save_report_to_global_list('-', private_key,
                                             '-', 'ERROR',
                                             '-', '-',
                                             'Some system error occurred during the process.')
            queue.task_done()


async def main():
    queue = asyncio.Queue(maxsize=NUMBER_OF_PROCESSES)
    pended = 0

    with open(TXT_WITH_PRIVATE_KEYS) as file:
        list_of_private_keys = [line.strip() for line in file.readlines()]

    producers = []
    for private_key in list_of_private_keys:
        pended += 1
        task = asyncio.create_task(producer(queue, private_key, pended))
        producers.append(task)

    consumers = []
    for _ in range(NUMBER_OF_PROCESSES):
        task = asyncio.create_task(consumer(queue, colors[random.choice(range(len(colors)))]))
        consumers.append(task)

    await asyncio.gather(*producers)
    await queue.join()

    for c in consumers:
        c.cancel()

    export_report()


if __name__ == '__main__':
    asyncio.run(main())

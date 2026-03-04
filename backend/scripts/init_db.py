from backend import database
import traceback

if __name__ == '__main__':
    try:
        print('Running database.init_db()...')
        database.init_db()
        print('init_db completed successfully')
    except Exception as e:
        print('init_db failed:')
        traceback.print_exc()

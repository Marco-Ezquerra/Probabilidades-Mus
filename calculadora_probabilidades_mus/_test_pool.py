import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'utils'))
import multiprocessing

def main():
    from generar_politicas_rollout import _worker_rollout
    print('Import OK')
    try:
        with multiprocessing.Pool(2) as pool:
            print('Pool created')
            results = pool.map(_worker_rollout, [(0, 1000, True, 42), (1, 1000, True, 43)])
            print('Pool finished, results:', len(results))
    except Exception as e:
        print('Pool ERROR:', e)
        import traceback; traceback.print_exc()

if __name__ == '__main__':
    main()

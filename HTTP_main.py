import threading
import time
import json
import redis

# Create Redis connection
redis_connection = redis.Redis()

def listen_predictions():
    while True:
        # Now start processing prediction tasks
        _, message = redis_connection.blpop("prediction")
        print(f"Received message from Redis: {message}")
        task = json.loads(message)
        print(f"Received task: {task}")
        task_id = task.get("task_id")
        redis_key = f"result:{task_id}"
        redis_value = json.dumps(task)
        redis_connection.set(redis_key, redis_value)
        for prediction in task['predictions']:
            print("Language: {}, Score: {:.4f}".format(prediction['label'], prediction['score']))

def perform_prediction(task):
    return task  # Here you might integrate your actual prediction model

if __name__ == "__main__":
    prediction_thread = threading.Thread(target=listen_predictions)
    prediction_thread.start()
"""Smoke test for fab-finder.

Checks three things before building the real app:
1. Chroma saves data to disk (run this twice; the count should stay the same).
2. The OpenAI embedding model works with my API key.
3. A Chinese query can find an English document by meaning.
"""

from pprint import pprint

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

STORE_PATH = "./chroma_store"
COLLECTION_NAME = "smoke_test"
EMBEDDING_MODEL = "text-embedding-3-small"
QUERY = "我要在木桌面中间挖一个很圆的大圆"

# Small hand-written items: (id, document text, domain)
ITEMS = [
    ("hole_saw",
     "A hole saw is a ring-shaped saw blade that attaches to a drill, with a small "
     "pilot bit in the center. It cuts clean round openings through wood, plastic "
     "or thin metal, for example for cable ports, pipes or door locks.",
     "woodworking"),
    ("jigsaw",
     "A jigsaw is a handheld power saw with a thin blade that moves up and down. "
     "It can follow curved lines and is used to cut shapes out of sheet material "
     "like plywood.",
     "woodworking"),
    ("cnc_router",
     "A CNC router is a computer-controlled cutting machine that moves a spinning "
     "bit along a programmed path to cut, carve or engrave sheets of wood, plastic "
     "or aluminum with high precision.",
     "woodworking"),
    ("pir_sensor",
     "A passive infrared (PIR) sensor measures infrared light radiating from "
     "objects in its field of view. It is commonly used in motion detectors to "
     "turn on lights or alarms when a person moves nearby.",
     "electronics"),
    ("ultrasonic_sensor",
     "An ultrasonic distance sensor sends out high-frequency sound pulses and "
     "times their echoes to measure how far away an object is.",
     "electronics"),
    ("arduino",
     "Arduino is a family of small programmable microcontroller boards that read "
     "inputs such as sensors and buttons and control outputs such as lights, "
     "motors and speakers.",
     "electronics"),
    ("led_strip",
     "An addressable LED strip is a flexible strip of LEDs where each light can be "
     "set to its own color and brightness by a microcontroller.",
     "lighting_display"),
    ("wood_screw",
     "A wood screw is a threaded fastener with a sharp point and coarse threads, "
     "designed to grip directly into wood and hold parts together.",
     "hardware"),
    ("threaded_insert",
     "A threaded insert is a metal sleeve installed into wood or plastic so that "
     "a machine bolt can be screwed in and removed many times without wearing out "
     "the material.",
     "hardware"),
    ("full_range_speaker",
     "A full-range speaker is a single loudspeaker driver designed to reproduce "
     "most of the audible frequency range, from bass to treble.",
     "audio"),
    ("audio_amplifier",
     "An audio amplifier boosts a weak audio signal from a source like a computer "
     "or media player so it is strong enough to drive loudspeakers.",
     "audio"),
    ("soldering_iron",
     "A soldering iron is a heated hand tool used to melt solder and join "
     "electronic components and wires together permanently.",
     "electronics"),
]


def main():
    # Read OPENAI_API_KEY from the .env file into the environment.
    load_dotenv()

    # 1. A client that writes to disk (not the in-memory default).
    client = chromadb.PersistentClient(path=STORE_PATH)

    # 2. OpenAI's embedding model. It reads the key from the OPENAI_API_KEY
    #    environment variable, so the key itself never appears in the code.
    embedder = embedding_functions.OpenAIEmbeddingFunction(
        model_name=EMBEDDING_MODEL,
        api_key_env_var="OPENAI_API_KEY",
    )

    # 3. The collection, using that model and cosine distance.
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedder,
        configuration={"hnsw": {"space": "cosine"}},
    )

    # 4. Add the items. Fixed ids, so a second run tries to add the same ids again.
    collection.add(
        ids=[item_id for item_id, _, _ in ITEMS],
        documents=[text for _, text, _ in ITEMS],
        metadatas=[{"domain": domain} for _, _, domain in ITEMS],
    )

    # 5. How many items are stored?
    print("Items in collection:", collection.count())

    # 6. Query in Chinese and print the full raw result.
    results = collection.query(query_texts=[QUERY], n_results=3)
    print("\nQuery:", QUERY)
    print("Raw result:")
    pprint(results)


if __name__ == "__main__":
    main()

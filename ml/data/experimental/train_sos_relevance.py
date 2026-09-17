"""Train and evaluate the SOS-specific relevance classifier."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "ml/data/experimental/sos_relevance.csv"
PANEL_PATH = ROOT / "ml/data/experimental/sos_relevance_panel.csv"
MODEL = ROOT / "ml/models/experimental/relevance_sos_candidate.joblib"
METRICS = ROOT / "ml/models/experimental/relevance_sos_candidate.metrics.json"


# Each pair is one semantic group. Both sides stay in the same split, preventing
# minimal-pair leakage while keeping both classes represented in every split.
PAIRS = [
    ("I am trapped inside my house", "The rescue drill had people pretending to be trapped inside the house"),
    ("my leg is injured and i need help now", "My friend hurt his leg last week and is fine now"),
    ("There is a fire in my building and I need help", "I watched a documentary about a building fire"),
    ("i cannot breathe and need someone to come", "The actor could not breathe in the movie scene"),
    ("We are stuck and cannot get out", "The hikers were stuck yesterday but reached home safely"),
    ("Please send rescue to this address", "The rescue team won an award last month"),
    ("Water is coming into my house", "Water entered the house during a film scene"),
    ("the road outside is completely blocked and i am stranded", "The road was blocked for a parade yesterday"),
    ("There is smoke everywhere and my family is inside", "The concert used smoke everywhere for special effects"),
    ("the building is shaking i dont know what to do", "The building shook during a special-effects test"),
    ("I don't know how to get out of this place", "The character did not know how to get out in the novel"),
    ("Power is gone and my elderly parents are inside", "Power was gone at the office but everyone went home"),
    ("help me im trapped on the upper floor", "The training video shows a person trapped on an upper floor"),
    ("my child is hurt and we cannot leave", "The child was hurt in a game yesterday and is fine"),
    ("please come quickly there are people injured here", "The article said people were injured years ago"),
    ("we need medical assistance at this location", "The clinic advertised medical assistance for routine visits"),
    ("I am bleeding badly please help", "The film showed a character bleeding badly"),
    ("my mother fell and cannot stand up", "My mother fell in a comedy and stood up afterward"),
    ("the flood water is entering our room", "The news report described flood water from last year"),
    ("we are surrounded by rising water", "The documentary showed a town surrounded by water"),
    ("the roof collapsed on us", "The roof collapsed in an old video but nobody was there"),
    ("I am inside the collapsed building", "Engineers discussed a collapsed building in class"),
    ("there is an active fire next door", "The museum exhibit explained an active fire from history"),
    ("my apartment is filling with smoke", "The theater apartment set was filling with smoke"),
    ("I am locked in and cannot escape", "The puzzle game requires players to escape a locked room"),
    ("send someone we are in danger", "The headline said the explorers were in danger in 2010"),
    ("my father is unconscious please call responders", "The show had an unconscious character"),
    ("we need evacuation from this street now", "The city posted an old evacuation plan"),
    ("the stairs are broken and we cannot leave", "The movie had broken stairs in an abandoned house"),
    ("I am hurt alone in my room", "The singer said he was hurt by criticism"),
    ("please help my family is still inside", "The family in the book stayed inside during the storm"),
    ("there are injured people beside me", "The report discussed injured people from a past event"),
    ("I have no way out of this flooded house", "The article described a flooded house after the event"),
    ("my child cannot breathe call for help", "The documentary explained why a child could not breathe"),
    ("we are cut off and need someone to reach us", "The village was cut off last winter but reopened"),
    ("fire is spreading toward our home", "The news replay showed fire spreading in another country"),
    ("i am shaking and scared please come", "The character was shaking before the competition"),
    ("my wheelchair cannot pass the debris", "The report said a wheelchair passed the debris safely"),
    ("there is gas and we need to leave immediately", "The lab lesson covered gas and emergency drills"),
    ("I need rescue from this room", "The rescue organization published its annual report"),
    ("help us the water is at the door", "The water was at the door in a suspense movie"),
    ("our building alarm is ringing and smoke is coming in", "The building alarm was tested successfully"),
    ("i fell and may have broken my arm", "The athlete broke his arm last season and recovered"),
    ("we cannot contact anyone and need help", "The article said the phones could not contact anyone during a festival"),
    ("someone is trapped under the fallen wall", "The construction report mentioned someone trapped years ago"),
    ("the storm damaged our home and we are inside", "The storm damaged homes in a historical report"),
    ("I am stranded here with no safe exit", "The traveler was stranded briefly but found a safe exit"),
    ("please get my grandparents out", "The grandparents got out safely in the story"),
    ("the floor is flooding and we are upstairs", "The floor was flooding in a museum demonstration"),
    ("there is a serious injury at my location", "The newspaper summarized a serious injury from yesterday"),
    ("we are stuck in the elevator send help", "The actor was stuck in an elevator in a comedy"),
    ("i smell smoke and cannot find the exit", "The movie character smelled smoke near an exit"),
    ("our house is on fire right now", "The documentary covered a house fire from decades ago"),
    ("I am having a seizure and need an ambulance", "The health article explained seizures in general"),
    ("the bridge is down and people are stranded here", "The bridge was down for repairs last summer"),
    ("my baby is ill and we need a doctor now", "The baby in the advertisement was ill in the storyline"),
    ("there are flames in the hallway", "The news archive showed flames in a hallway"),
    ("i am lost after the earthquake and cannot reach home", "The earthquake documentary described people who later reached home"),
    ("we have no food or water and are trapped", "The charity campaign collects food and water"),
    ("the ceiling is falling please come", "The theater ceiling was falling in a stunt scene"),
    ("my brother is bleeding and alone", "The book described a brother bleeding after a battle"),
    ("I cannot move my legs after the crash", "The interviewee could not move his legs before surgery years ago"),
    ("please answer we are trapped in this room", "The escape-room game says players are trapped in a room"),
    ("the fire alarm is real and smoke is entering", "The fire alarm test was announced by the school"),
    ("I need immediate help at my location", "The help desk offers immediate help with homework"),
    ("someone is drowning near me", "The film scene showed someone drowning"),
    ("we are under debris and cannot get out", "The report described debris after an old earthquake"),
    ("the road washed away and our car is stuck", "The road washed away during last year's storm"),
    ("my chest hurts and i cannot breathe", "The article explained why chest pain can happen"),
    ("we need responders at the building now", "The responders attended a conference at the building"),
    ("there is a landslide blocking our only exit", "The documentary showed a landslide blocking a road"),
    ("i am alone and terrified in the dark building", "The horror movie had a terrified person in a dark building"),
    ("please evacuate us the water keeps rising", "The city website explains how to evacuate during floods"),
    ("water is pouring through our doorway and we cannot leave", "The flood article says water once poured through a doorway"),
    ("the storm washed away the road and we are cut off", "The travel blog says the storm washed away a road last year"),
    ("I need help getting out of this burning room", "The fire drill teaches students how to get out of a room"),
    ("my ankle is hurt and I am alone with no transport", "My cousin hurt an ankle last month and is walking normally"),
    ("please help us the smoke is getting thicker", "The theater used thicker smoke for the final scene"),
    ("my phone has no signal and the house is filling with water", "The phone review says it has no signal in some houses"),
    ("we are safe but the flood happened yesterday", "We are safe now after yesterday's flood"),
    ("I cannot breathe properly and nobody is here", "The health guide explains that some people cannot breathe properly"),
    ("there is a fire drill at school this afternoon", "The school fire drill was completed without problems"),
    ("help me carry these books for homework", "Can you help me with my homework tonight"),
    ("my charger is broken and I need help finding one", "Customer support can help find a phone charger"),
    ("happy birthday to my brother hope you have fun", "Happy birthday to everyone in the group"),
    ("the bridge fell and we cannot reach the town", "The bridge was closed for repairs but traffic used another route"),
    ("I saw a rescue helicopter while watching television", "A rescue helicopter appeared in the documentary"),
    ("the weather is lovely and the roads are clear", "The weather forecast says the roads will be clear"),
    ("my sister is locked inside and calling for help", "The game asks players to unlock a sister's room"),
    ("smoke is entering our apartment and we need out", "The movie shows smoke entering an apartment"),
    ("the river is around the house and still rising", "A documentary shows a river around a house"),
    ("I am stuck in traffic but everyone is safe", "The driver was stuck in traffic for ten minutes"),
    ("my grandmother fell and cannot get up", "The actress fell during rehearsal and got up safely"),
    ("the building is shaking and the ceiling is cracking", "The building shook during a controlled engineering test"),
    ("please send help our only exit is blocked", "The website explains how emergency exits are inspected"),
    ("we need an ambulance for my child right now", "The clinic article describes when children need ambulances"),
    ("the news says a fire happened in another city", "The news report discussed a fire that was contained yesterday"),
    ("I need help right now, the ceiling is coming down", "I need help choosing a color for my bedroom"),
    ("the water is at our knees and rising fast", "The swimming pool water is at my knees"),
    ("please get here, my sister is trapped behind the door", "The video game says my sister is trapped behind a door"),
    ("our street vanished under mud and we are still here", "The travel article describes a street covered in mud"),
    ("I am coughing and the room is full of smoke", "The chef says the room was full of smoke while cooking"),
    ("my son is injured and there is no car to take him", "My son was injured in a match and returned to school"),
    ("we cannot leave because the flames are outside", "The lesson explains why flames spread outside a building"),
    ("someone in this house is unconscious", "The television episode had an unconscious person"),
    ("I have been calling but nobody can reach us", "The phone company says callers could not reach the office"),
    ("the road is gone and our vehicle cannot move", "The road is gone for construction next week"),
    ("there is no safe way down from this roof", "The building guide describes a safe way down from a roof"),
    ("my chest hurts and I am alone here", "The doctor wrote about chest pain in a general guide"),
    ("we are surrounded by floodwater and need a boat", "The harbor rents boats for floodwater photography"),
    ("the alarm is sounding and I can see flames", "The alarm sounded during a planned test"),
    ("I fell hard and cannot stand", "The actor fell hard during a stunt and stood afterward"),
    ("send help to the house at the end of the road", "The help page gives directions to the house at the end of the road"),
    ("the elevator stopped and there are children inside", "The elevator stopped briefly during maintenance"),
    ("I am lost in the smoke and cannot find my door", "The magician lost a prop in stage smoke"),
    ("we need to leave now, the river reached the stairs", "The river reached the stairs in a photograph"),
    ("please call an ambulance, my mother is not responding", "The ambulance service wrote an informational article"),
    ("there is debris across the entrance and we are inside", "The cleanup crew moved debris across the entrance"),
    ("the storm is breaking windows while we are indoors", "The weather report says the storm broke windows yesterday"),
    ("my breathing is getting worse and I need a doctor", "The medical article explains why breathing can get worse"),
    ("I cannot open the door and smoke is coming under it", "The escape-room puzzle has smoke coming under a door"),
    ("the hillside collapsed beside us and we are cut off", "The geography lesson describes a hillside that collapsed"),
]

PANEL_CASES = [
    ("I hurt my leg and I'm stuck upstairs", "relevant"),
    ("cant get out pls send somebody", "relevant"),
    ("Smoke is filling the kitchen, what do I do", "relevant"),
    ("my dad fell and wont wake up", "relevant"),
    ("water through the front door rn", "relevant"),
    ("We are safe now, just reporting yesterday's flood", "not_relevant"),
    ("Does anyone know a good disaster movie?", "not_relevant"),
    ("The emergency drill at school went well", "not_relevant"),
    ("my cousin had a broken leg but is recovered", "not_relevant"),
    ("News says a fire happened across the border", "not_relevant"),
    ("pls help me finish this homework", "not_relevant"),
    ("building a model house for class", "not_relevant"),
    ("I cannot find my way out of this unfamiliar station", "relevant"),
    ("elderly neighbors are inside and the power is out", "relevant"),
    ("there was smoke earlier but it is gone and everyone left", "not_relevant"),
    ("the river is rising around our only road", "relevant"),
    ("Happy birthday to my sister", "not_relevant"),
    ("my phone is dying and I need a charger", "not_relevant"),
    ("fire drill starts at ten", "not_relevant"),
    ("we're trapped by rubble, no signal", "relevant"),
    ("I saw a rescue helicopter on television", "not_relevant"),
    ("please help, my ankle is badly swollen and I am alone", "relevant"),
    ("The weather is lovely today", "not_relevant"),
    ("there is a strange smell and everyone is coughing", "relevant"),
    ("the report says buildings shook overnight", "not_relevant"),
    ("cant breathe well call ambulance", "relevant"),
    ("the rescue drill had realistic smoke", "not_relevant"),
    ("our only bridge disappeared in the storm", "relevant"),
    ("I watched a disaster documentary", "not_relevant"),
    ("someone is yelling for help next door", "relevant"),
    ("help choosing a birthday gift", "not_relevant"),
    ("im stuck in traffic but safe", "not_relevant"),
    ("my sister is locked inside and crying", "relevant"),
]


def make_dataset() -> pd.DataFrame:
    rows = []
    for index, (relevant, negative) in enumerate(PAIRS, start=1):
        rows.extend(
            [
                {"text": relevant, "label": "relevant", "group_id": f"pair-{index:03d}"},
                {"text": negative, "label": "not_relevant", "group_id": f"pair-{index:03d}"},
            ]
        )
    return pd.DataFrame(rows)


def metrics(pipeline: Pipeline, frame: pd.DataFrame) -> dict:
    predictions = pipeline.predict(frame["text"])
    labels = list(pipeline.named_steps["classifier"].classes_)
    precision, recall, f1, support = precision_recall_fscore_support(
        frame["label"], predictions, labels=labels, zero_division=0
    )
    return {
        "accuracy": float(accuracy_score(frame["label"], predictions)),
        "precision_macro": float(precision.mean()),
        "recall_macro": float(recall.mean()),
        "f1_macro": float(f1.mean()),
        "per_class": {
            label: {
                "precision": float(precision[i]),
                "recall": float(recall[i]),
                "f1": float(f1[i]),
                "support": int(support[i]),
            }
            for i, label in enumerate(labels)
        },
        "confusion_matrix": confusion_matrix(frame["label"], predictions, labels=labels).tolist(),
        "labels": labels,
        "false_negatives": [
            {"text": text, "expected": expected, "predicted": predicted}
            for text, expected, predicted in zip(frame["text"], frame["label"], predictions)
            if expected == "relevant" and predicted == "not_relevant"
        ],
        "false_positives": [
            {"text": text, "expected": expected, "predicted": predicted}
            for text, expected, predicted in zip(frame["text"], frame["label"], predictions)
            if expected == "not_relevant" and predicted == "relevant"
        ],
    }


def main() -> None:
    dataset = make_dataset()
    DATASET.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(DATASET, index=False)
    PANEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(PANEL_CASES, columns=["text", "label"]).to_csv(PANEL_PATH, index=False)

    first_train, held_out = next(
        GroupShuffleSplit(n_splits=1, test_size=0.30, random_state=42).split(
            dataset["text"], dataset["label"], dataset["group_id"]
        )
    )
    train_frame = dataset.iloc[first_train]
    held_out_frame = dataset.iloc[held_out]
    validation_index, test_index = next(
        GroupShuffleSplit(n_splits=1, test_size=0.50, random_state=43).split(
            held_out_frame["text"], held_out_frame["label"], held_out_frame["group_id"]
        )
    )
    validation = held_out_frame.iloc[validation_index]
    test = held_out_frame.iloc[test_index]

    pipeline = Pipeline(
        [
            (
                "tfidf",
                FeatureUnion(
                    [
                        (
                            "word",
                            TfidfVectorizer(
                                ngram_range=(1, 2), sublinear_tf=True, max_features=5000
                            ),
                        ),
                        (
                            "char",
                            TfidfVectorizer(
                                analyzer="char_wb",
                                ngram_range=(3, 5),
                                sublinear_tf=True,
                                max_features=5000,
                            ),
                        ),
                    ]
                ),
            ),
            ("classifier", LinearSVC(class_weight="balanced", random_state=42)),
        ]
    )
    pipeline.fit(train_frame["text"], train_frame["label"])
    panel_frame = pd.read_csv(PANEL_PATH)
    report = {
        "dataset": str(DATASET.relative_to(ROOT)),
        "dataset_size": len(dataset),
        "class_balance": dataset["label"].value_counts().to_dict(),
        "split": {
            "train": len(train_frame),
            "validation": len(validation),
            "test": len(test),
            "train_groups": train_frame["group_id"].nunique(),
            "validation_groups": validation["group_id"].nunique(),
            "test_groups": test["group_id"].nunique(),
            "group_overlap": False,
        },
        "model": "TfidfVectorizer word unigrams/bigrams + balanced LinearSVC",
        "validation": metrics(pipeline, validation),
        "test": metrics(pipeline, test),
        "panel": metrics(pipeline, panel_frame),
    }
    joblib.dump(pipeline, MODEL)
    METRICS.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

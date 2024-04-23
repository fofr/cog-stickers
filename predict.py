import os
import shutil
import json
import random
from typing import List
from cog import BasePredictor, Input, Path
from helpers.comfyui import ComfyUI

OUTPUT_DIR = "/tmp/outputs"
INPUT_DIR = "/tmp/inputs"
COMFYUI_TEMP_OUTPUT_DIR = "ComfyUI/temp"

with open("sticker_maker_api.json", "r") as file:
    workflow_json = file.read()


class Predictor(BasePredictor):
    def setup(self):
        self.comfyUI = ComfyUI("127.0.0.1:8188")
        self.comfyUI.start_server(OUTPUT_DIR, INPUT_DIR)
        self.comfyUI.load_workflow(workflow_json)

    def cleanup(self):
        self.comfyUI.clear_queue()
        for directory in [OUTPUT_DIR, INPUT_DIR, COMFYUI_TEMP_OUTPUT_DIR]:
            if os.path.exists(directory):
                shutil.rmtree(directory)
            os.makedirs(directory)

    def update_workflow(self, workflow, **kwargs):
        workflow["6"]["inputs"]["text"] = (
            f"Sticker, {kwargs.get('prompt')}, svg, solid color background"
        )
        workflow["7"]["inputs"]["text"] = (
            f"nsfw, nude, {kwargs.get('negative_prompt')}, photo, photography"
        )

        empty_latent_image = workflow["5"]["inputs"]
        empty_latent_image["width"] = kwargs.get("width")
        empty_latent_image["height"] = kwargs.get("height")
        empty_latent_image["batch_size"] = kwargs.get("number_of_images")

        scheduler = workflow["3"]["inputs"]
        scheduler["seed"] = kwargs.get("seed")
        scheduler["steps"] = kwargs.get("steps")

    def log_and_collect_files(self, directory, prefix=""):
        files = []
        for f in os.listdir(directory):
            if f == "__MACOSX":
                continue
            path = os.path.join(directory, f)
            if os.path.isfile(path):
                print(f"{prefix}{f}")
                files.append(Path(path))
            elif os.path.isdir(path):
                print(f"{prefix}{f}/")
                files.extend(self.log_and_collect_files(path, prefix=f"{prefix}{f}/"))
        return files

    def predict(
        self,
        prompt: str = Input(default="a cute cat"),
        negative_prompt: str = Input(
            default="",
            description="Things you do not want in the image",
        ),
        width: int = Input(default=1152),
        height: int = Input(default=1152),
        steps: int = Input(default=17),
        number_of_images: int = Input(
            default=1, ge=1, le=10, description="Number of images to generate"
        ),
        seed: int = Input(
            default=None, description="Fix the random seed for reproducibility"
        ),
    ) -> List[Path]:
        """Run a single prediction on the model"""
        self.cleanup()

        if seed is None:
            seed = random.randint(0, 2**32 - 1)
            print(f"Random seed set to: {seed}")

        workflow = json.loads(workflow_json)

        self.update_workflow(
            workflow,
            width=width,
            height=height,
            steps=steps,
            prompt=prompt,
            negative_prompt=negative_prompt,
            number_of_images=number_of_images,
            seed=seed,
        )

        wf = self.comfyUI.load_workflow(workflow)
        self.comfyUI.connect()
        self.comfyUI.run_workflow(wf)

        files = []
        output_directories = [OUTPUT_DIR]

        for directory in output_directories:
            print(f"Contents of {directory}:")
            files.extend(self.log_and_collect_files(directory))

        return files

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

with open("workflow.json", "r") as file:
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

    def update_workflow(
        self,
        workflow,
        width,
        height,
        steps,
        prompt,
        negative_prompt,
        seed,
        upscale_steps,
        is_upscale,
    ):
        loader = workflow["2"]["inputs"]
        loader["empty_latent_width"] = width
        loader["empty_latent_height"] = height
        loader["positive"] = f"Sticker, {prompt}, svg, solid color background"
        loader["negative"] = f"nsfw, nude, {negative_prompt}, photo, photography"

        sampler = workflow["4"]["inputs"]
        sampler["seed"] = seed
        sampler["steps"] = steps

        upscaler = workflow["11"]["inputs"]
        if is_upscale:
            del workflow["5"]
            del workflow["10"]
            upscaler["steps"] = upscale_steps
            upscaler["seed"] = seed
        else:
            del workflow["16"]
            del workflow["17"]
            del workflow["18"]
            del upscaler["image"]
            del upscaler["model"]
            del upscaler["positive"]
            del upscaler["negative"]
            del upscaler["vae"]

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
        width: int = Input(default=1024),
        height: int = Input(default=1024),
        steps: int = Input(default=20),
        seed: int = Input(
            default=None, description="Fix the random seed for reproducibility"
        ),
        upscale: bool = Input(default=True, description="2x upscale the sticker"),
        upscale_steps: int = Input(
            default=10, description="Number of steps to upscale"
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
            width,
            height,
            steps,
            prompt,
            negative_prompt,
            seed,
            upscale_steps,
            is_upscale=upscale,
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

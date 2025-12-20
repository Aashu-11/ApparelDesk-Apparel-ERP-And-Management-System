import os
import cv2
import gradio as gr
import numpy as np
import random
import time
from PIL import Image
import io
from gradio_client import Client, handle_file
import tempfile

# ============================================
# Hugging Face Inference API (IDM-VTON)
# Uses the free HF Inference API - no API key needed!
# ============================================
print("Initializing Hugging Face Inference API client...")

# Initialize the client for IDM-VTON (free tier)
try:
    hf_client = Client("yisol/IDM-VTON")
    print("[OK] Connected to IDM-VTON Inference API")
    API_AVAILABLE = True
except Exception as e:
    print(f"[WARN] Could not connect to API: {e}")
    print("Falling back to stub mode")
    hf_client = None
    API_AVAILABLE = False


def tryon(person_img, garment_img, seed, randomize_seed):
    """
    Virtual try-on using Hugging Face Inference API (IDM-VTON).
    No local GPU required - uses cloud inference.
    """
    if person_img is None or garment_img is None:
        gr.Warning("Empty image")
        return None, None, "Empty image"
    
    if randomize_seed:
        seed = random.randint(0, MAX_SEED)
    
    # If API not available, return stub
    if not API_AVAILABLE or hf_client is None:
        return person_img, seed, "API not available - returning original"
    
    try:
        start_time = time.time()
        print(f"Starting inference with seed {seed}...")
        
        # Convert numpy arrays to PIL and save to temp files
        person_pil = Image.fromarray(person_img).convert("RGB")
        garment_pil = Image.fromarray(garment_img).convert("RGB")
        
        # Save to temporary files (required for gradio_client)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as person_file:
            person_pil.save(person_file.name)
            person_path = person_file.name
        
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as garment_file:
            garment_pil.save(garment_file.name)
            garment_path = garment_file.name
        
        # Call the IDM-VTON API
        # API signature: process_dc(dict, garm_img, garment_des, is_checked, is_checked_crop, denoise_steps, seed)
        result = hf_client.predict(
            dict(background=handle_file(person_path), layers=[], composite=None),  # person image dict
            handle_file(garment_path),  # garment image
            "A stylish garment",  # garment description
            True,   # is_checked (auto-mask)
            True,   # is_checked_crop (auto-crop)
            30,     # denoise_steps
            seed,   # seed
            api_name="/tryon"
        )
        
        # Clean up temp files
        os.unlink(person_path)
        os.unlink(garment_path)
        
        # The result is a tuple, first element is the output image path
        if result and len(result) > 0:
            result_path = result[0]
            result_img = np.array(Image.open(result_path).convert("RGB"))
            
            end_time = time.time()
            inference_time = end_time - start_time
            
            return result_img, seed, f"Success! ({inference_time:.1f}s)"
        else:
            return person_img, seed, "No result returned from API"
        
    except Exception as e:
        print(f"Inference error: {e}")
        # Clean up temp files on error
        try:
            if 'person_path' in locals():
                os.unlink(person_path)
            if 'garment_path' in locals():
                os.unlink(garment_path)
        except:
            pass
        return person_img, seed, f"Error: {str(e)}"

def start_tryon(person_img, garment_img, seed, randomize_seed):
    start_time = time.time()
    if person_img is None or garment_img is None:
        return None, None, "Empty image"
    if randomize_seed:
        seed = random.randint(0, MAX_SEED)
    encoded_person_img = cv2.imencode('.jpg', cv2.cvtColor(person_img, cv2.COLOR_RGB2BGR))[1].tobytes()
    encoded_person_img = base64.b64encode(encoded_person_img).decode('utf-8')
    encoded_garment_img = cv2.imencode('.jpg', cv2.cvtColor(garment_img, cv2.COLOR_RGB2BGR))[1].tobytes()
    encoded_garment_img = base64.b64encode(encoded_garment_img).decode('utf-8')

    url = "http://" + os.environ['tryon_url']
    token = os.environ['token']
    cookie = os.environ['Cookie']
    referer = os.environ['referer']

    headers = {'Content-Type': 'application/json', 'token': token, 'Cookie': cookie, 'referer': referer}
    data = {
        "clothImage": encoded_garment_img,
        "humanImage": encoded_person_img,
        "seed": seed
    }

    result_img = None
    try:
        session = requests.Session()
        response = session.post(url, headers=headers, data=json.dumps(data), timeout=60)
        print("response code", response.status_code)
        if response.status_code == 200:
            result = response.json()['result']
            status = result['status']
            if status == "success":
                result = base64.b64decode(result['result'])
                result_np = np.frombuffer(result, np.uint8)
                result_img = cv2.imdecode(result_np, cv2.IMREAD_UNCHANGED)
                result_img = cv2.cvtColor(result_img, cv2.COLOR_RGB2BGR)
                info = "Success"
            else:
                info = "Try again latter"
        else:
            print(response.text)
            info = "URL error, pleace contact the admin"
    except requests.exceptions.ReadTimeout:
        print("timeout")
        info = "Too many users, please try again later"
        raise gr.Error("Too many users, please try again later")
    except Exception as err:
        print(f"其他错误: {err}")
        info = "Error, pleace contact the admin"
    end_time = time.time()
    print(f"time used: {end_time-start_time}")

    return result_img, seed, info

MAX_SEED = 999999

example_path = os.path.join(os.path.dirname(__file__), 'assets')

garm_list = os.listdir(os.path.join(example_path,"cloth"))
garm_list_path = [os.path.join(example_path,"cloth",garm) for garm in garm_list]

human_list = os.listdir(os.path.join(example_path,"human"))
human_list_path = [os.path.join(example_path,"human",human) for human in human_list]

css="""
/* ===== IMPORT FONTS ===== */
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@300;400;500;600&display=swap');

/* ===== WHITE GRID BACKGROUND - TARGET ALL POSSIBLE CONTAINERS ===== */
body, html {
    background-color: #f5f5f5 !important;
    background-image: 
        linear-gradient(rgba(0,0,0,0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,0,0,0.05) 1px, transparent 1px) !important;
    background-size: 40px 40px !important;
    background-attachment: fixed !important;
}

.gradio-container,
.gradio-container-6-2-0,
[class*="gradio-container"] {
    background-color: #f5f5f5 !important;
    background-image: 
        linear-gradient(rgba(0,0,0,0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,0,0,0.05) 1px, transparent 1px) !important;
    background-size: 40px 40px !important;
    background-attachment: fixed !important;
    min-height: 100vh;
    font-family: 'Inter', sans-serif !important;
}

/* Make all inner containers transparent */
.gradio-container > div,
.gradio-container-6-2-0 > div,
.contain, .wrap, .block, .form, .gap, .panel, .main, .app {
    background: transparent !important;
}

/* ===== COLUMN CARDS - BLACK WITH GRID ===== */
#col-left, #col-mid, #col-right {
    margin: 0 auto;
    max-width: 430px;
    background-color: #0a0a0a !important;
    background-image: 
        linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px) !important;
    background-size: 30px 30px !important;
    border-radius: 0px;
    padding: 25px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2);
}

#col-showcase {
    margin: 0 auto;
    max-width: 1100px;
    background-color: #0a0a0a !important;
    background-image: 
        linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px) !important;
    background-size: 30px 30px !important;
    border-radius: 0px;
    padding: 30px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* ===== RUN BUTTON ===== */
#button {
    background: #1a1a1a !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 14px 40px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: 3px !important;
    text-transform: uppercase !important;
    color: white !important;
    cursor: pointer !important;
    transition: all 0.3s ease !important;
}

#button:hover {
    background: #333 !important;
}

/* ===== IMAGE AREAS - DARK STYLE ===== */
.image-container, .upload-container, .image-frame, .svelte-1pijsyv {
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 4px !important;
    background: rgba(255, 255, 255, 0.05) !important;
}

/* ===== INPUTS - DARK STYLE ===== */
input[type="range"] {
    accent-color: #fff !important;
}

input, textarea, select {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 0px !important;
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
}

/* ===== LABELS - WHITE TEXT ===== */
label, .label-wrap, span.svelte-1gfkn6j {
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 400 !important;
    background: transparent !important;
}

/* ===== GALLERY ===== */
.gallery, .gallery-item, .thumbnail-item {
    background: transparent !important;
}

/* ===== FOOTER ===== */
footer, .footer {
    background: transparent !important;
}
"""

def load_description(fp):
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def change_imgs(image1, image2):
    return image1, image2

with gr.Blocks() as Tryon:
    # Inject CSS as style tag
    gr.HTML(f"<style>{css}</style>")
    gr.HTML(load_description("assets/title.md"))
    with gr.Row():
        with gr.Column(elem_id = "col-left"):
            gr.HTML("""
            <div style="text-align: center; padding: 20px;">
                <span style="font-family: 'Anton', sans-serif; font-size: 24px; color: #fff; letter-spacing: 2px;">
                    01. PERSON
                </span>
                <p style="font-family: 'Inter', sans-serif; color: #666; font-size: 12px; margin-top: 8px; letter-spacing: 1px;">Full body photo works best</p>
            </div>
            """)
        with gr.Column(elem_id = "col-mid"):
            gr.HTML("""
            <div style="text-align: center; padding: 20px;">
                <span style="font-family: 'Anton', sans-serif; font-size: 24px; color: #fff; letter-spacing: 2px;">
                    02. GARMENT
                </span>
                <p style="font-family: 'Inter', sans-serif; color: #666; font-size: 12px; margin-top: 8px; letter-spacing: 1px;">Any clothing item</p>
            </div>
            """)
        with gr.Column(elem_id = "col-right"):
            gr.HTML("""
            <div style="text-align: center; padding: 20px;">
                <span style="font-family: 'Anton', sans-serif; font-size: 24px; color: #fff; letter-spacing: 2px;">
                    03. RESULT
                </span>
                <p style="font-family: 'Inter', sans-serif; color: #666; font-size: 12px; margin-top: 8px; letter-spacing: 1px;">AI-generated try-on</p>
            </div>
            """)
    with gr.Row():
        with gr.Column(elem_id = "col-left"):
            imgs = gr.Image(label="Person image", type="numpy")
            # category = gr.Dropdown(label="Garment category", choices=['upper_body', 'lower_body', 'dresses'],  value="upper_body")
            example = gr.Examples(
                inputs=imgs,
                examples_per_page=12,
                examples=human_list_path
            )
        with gr.Column(elem_id = "col-mid"):
            garm_img = gr.Image(label="Garment image", type="numpy")
            example = gr.Examples(
                inputs=garm_img,
                examples_per_page=12,
                examples=garm_list_path
            )
        with gr.Column(elem_id = "col-right"):
            image_out = gr.Image(label="Result")
            with gr.Row():
                seed = gr.Slider(
                    label="Seed",
                    minimum=0,
                    maximum=MAX_SEED,
                    step=1,
                    value=0,
                )
                randomize_seed = gr.Checkbox(label="Random seed", value=True)
            with gr.Row():
                seed_used = gr.Number(label="Seed used")
                result_info = gr.Text(label="Response")
            # try_button = gr.Button(value="Run", elem_id="button")
            test_button = gr.Button(value="Run", elem_id="button")


    # try_button.click(fn=start_tryon, inputs=[imgs, garm_img, seed, randomize_seed], outputs=[image_out, seed_used, result_info], api_name='tryon',concurrency_limit=10)
    test_button.click(fn=tryon, inputs=[imgs, garm_img, seed, randomize_seed], outputs=[image_out, seed_used, result_info], api_name=False, concurrency_limit=45)

    with gr.Column(elem_id = "col-showcase"):
        gr.HTML("""
        <div style="display: flex; justify-content: center; align-items: center; text-align: center; font-size: 20px;">
            <div> </div>
            <br>
            <div>
            Virtual try-on examples in pairs of person and garment images
            </div>
        </div>
        """)
        show_case = gr.Examples(
            examples=[
                ["assets/examples/model2.png", "assets/examples/garment2.png", "assets/examples/result2.png"],
                ["assets/examples/model3.png", "assets/examples/garment3.png", "assets/examples/result3.png"],
                ["assets/examples/model1.png", "assets/examples/garment1.png", "assets/examples/result1.png"],
            ],
            inputs=[imgs, garm_img, image_out],
            label=None
        )
    
    # Footer
    gr.HTML("""
    <div style="background: transparent; padding: 60px 20px; margin-top: 50px; border-top: 1px solid rgba(0,0,0,0.1);">
        <div style="max-width: 1100px; margin: 0 auto; text-align: center;">
            <!-- Brand -->
            <h2 style="font-family: 'Anton', sans-serif; font-size: 32px; color: #1a1a1a; margin: 0; letter-spacing: 3px;">
                VIRTUAL TRY-ON
            </h2>
            <p style="font-family: 'Inter', sans-serif; color: #888; font-size: 11px; margin-top: 10px; letter-spacing: 2px;">
                AI-POWERED FASHION TECHNOLOGY
            </p>
            
            <!-- Links -->
            <div style="display: flex; justify-content: center; gap: 50px; flex-wrap: wrap; margin: 40px 0;">
                <div>
                    <p style="font-family: 'Inter', sans-serif; color: #aaa; font-size: 10px; letter-spacing: 2px; margin-bottom: 8px;">POWERED BY</p>
                    <a href="https://huggingface.co/yisol/IDM-VTON" target="_blank" style="font-family: 'Inter', sans-serif; color: #1a1a1a; text-decoration: none; font-size: 13px; border-bottom: 1px solid #1a1a1a;">IDM-VTON</a>
                </div>
                <div>
                    <p style="font-family: 'Inter', sans-serif; color: #aaa; font-size: 10px; letter-spacing: 2px; margin-bottom: 8px;">PLATFORM</p>
                    <a href="https://huggingface.co" target="_blank" style="font-family: 'Inter', sans-serif; color: #1a1a1a; text-decoration: none; font-size: 13px; border-bottom: 1px solid #1a1a1a;">Hugging Face</a>
                </div>
                <div>
                    <p style="font-family: 'Inter', sans-serif; color: #aaa; font-size: 10px; letter-spacing: 2px; margin-bottom: 8px;">FRAMEWORK</p>
                    <a href="https://gradio.app" target="_blank" style="font-family: 'Inter', sans-serif; color: #1a1a1a; text-decoration: none; font-size: 13px; border-bottom: 1px solid #1a1a1a;">Gradio</a>
                </div>
            </div>
            
            <!-- Copyright -->
            <p style="font-family: 'Inter', sans-serif; color: #bbb; font-size: 10px; letter-spacing: 1px;">
                Built with AI | Virtual Try-On Demo
            </p>
        </div>
    </div>
    """)

Tryon.launch()

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from bs4 import BeautifulSoup
import os
import asyncio
import re
import pandas as pd
from chat.openai_api_chat import OpenaiAPIChat
from prompts.review_prompts import *
from prompts.improve_prompts import *
from config import translate_config as conf
from pages.general_functions import *
import json
import shutil
from datetime import datetime


def system_prompt():
    '''
    The character assigned to LLM for Translation Review.
    :return: Formatted system prompt string in JSON format
    '''
    system_prompt = {
        "role": "String Classification Expert",
        "classification": {
            'General Element': None,
            'Photo Recommendation': "To get the best result, use a photo with which content and avoid which content.", 
            'PowerDirector Launcher': 'The PowerDirector launcher is displayed when you launch the program from the start menu or desktop shortcut.\nIt provides quick access to popular features.\nYou can click "New Project" to open PowerDirector and start a new video project.\nYou can also quickly access "Recent Projects" or click "Open Project" to open and edit previously worked-on video projects.\nBefore clicking "New Project", ensure you set the Aspect Ratio for your project. Available ratios are 16:9, 21:9, 1:1, 4:5, 9:16, or 4:3.\nYou can deselect the "Show launcher after closing program" option if you do not want it to display when closing the program.',
            'Workspace': 'The workspace is the area where you will spend most of your time in CyberLink PowerDirector, and it is recommended to get familiar with its features.\nThe CyberLink PowerDirector workspace is fully expandable and customizable based on personal preference.\nYou can resize the preview window and timeline by dragging their borders.\nThe editing workspace can be customized by undocking and moving the library window, timeline, and preview windows.\nKey components of the workspace include:\nA - Rooms\nB - Import Media\nC - Library Window\nD - Expandable Workspace\nE - Library Preview Window\nF - Project Preview Window\nG - Timeline/Editing Workspace\nH - Range Selection\nI - Function Buttons\nJ - Timeline Ruler\nK - Nested Projects/Sequences\nL - View Entire Video\nM - Track Manager',
            'Modules': {
                'Edit Module': 'In this module, you can edit and trim imported media, arrange it in your video production, and add effects, titles, PiP objects, transitions, music, and subtitles.',
                'Export Module': 'In this module, you can output your created production to a video file or upload it to YouTube and Vimeo.'
            },
            'Rooms': {
                'Media Room': 'The media library contains video, audio, and image files you have imported into PowerDirector.\nYou can also directly access asset folders containing useful color boards, your saved projects, and background music/sound clips.',
                'Video Intro/Outro Room': 'Click the associated button to open this room and use video intro or outro templates to start or close your video project.\nTemplates can be added directly to the timeline or customized in the Video Intro/Outro Designer.',
                'Title Room': 'Click the associated button to open the Title Room and view the library of title effects.\nThese effects allow you to add video titles, screen captions, credits, etc. on your videos.',
                'Transition Room': 'Click the associated button to open the Transition Room, which contains transitions you can use on or between clips in your project.'
            },
            'Effects': {
                'Effect Room': 'Click the associated button to open the Effect Room, which contains a library of special effects used on video files and images in your project.',
                'Video Style Effects': 'Accessed via the "Style Effect" tag, these are over 100 effects like mosaic, blur, and black & white conversion.',
                'Color LUT': 'Accessed via the "Color LUT" tag, these transform the range of colors in a video clip to another range, changing the color scheme or ensuring consistent look.',
                'Body Effects': 'Accessed via "Body Effect", these apply custom effects to objects (people, pets, etc.) detected by PowerDirector\'s AI engine in video clips.'
            },
            'PiP Objects': {
                'PiP Objects Room': 'Click the associated button to open this room, which contains a library of PiP objects, or graphics, that can be added on top of the video or images on a video track.',
                'Motion Graphics PiP Objects': 'Found by clicking the button and selecting the "Motion Graphics" tag (often searchable as "Social Motion Graphics"). These objects contain animated graphics that can be customized.',
                'Creating Custom PiP Objects': 'Open the Video Overlays room, click the "Create new PiP object" button, and select an image file to import and open in the PiP Designer for editing.'
            },
            'Audio': {
                'Audio Mixing Room': 'Click the associated button to open the Audio Mixing Room. This room provides controls to mix all of the audio tracks in your project.',
                'Voice-Over Recording Room': 'Click the associated button to open the Voice-Over Recording Room. Here, you can record a voice-over for your video production while watching it play back.',
                'Audio Editor': 'To access it, select an audio or video clip (with audio) on the timeline, click the Tools button above the timeline, and then select Audio Editor. In the Audio Editor, you can decide whether to apply edits to all available channels or only one.'
            },
            'Subtitle Room': {
                'Manual Subtitles': 'You can create subtitles manually by selecting the video or audio clip on the timeline, clicking "Create Subtitles Manually", and using player controls to find positions for subtitles.',
                'Importing Subtitles': 'You can import subtitles composed outside the program or from other sources. Supported formats: SRT or TXT.',
                'Syncing Subtitles': 'Adjust the start and end time for each subtitle marker by double-clicking the "Start Time" or "End Time" columns or dragging the beginning/end of the subtitle marker.'
            },
            'Library Window': 'The library window contains all of the media in CyberLink PowerDirector, including your video, images, and audio files. You can resize the media thumbnails by clicking the button and selecting a default size from the library menu.',
            'Display Preferences': 'Accessed by clicking the Preferences button and selecting the Display tab. Available options include setting the timeline preview quality and enabling snap to reference lines.',
            'Project Preferences': 'Accessed by clicking the Preferences button and selecting the Project tab. You can set preferences for recently used projects, auto-saving, and project loading.',
            'Editing Preferences': 'Accessed by clicking the Preferences button and selecting the Editing tab. Available options include setting default transition behavior, enabling snap to clips in timeline, and adjusting the duration settings.',
            'Produce Preferences': 'Accessed by selecting "Preferences" from the PowerDirector menu and then the Export tab. You can choose whether to import exported files into the media room.',
            'Performance Preferences': 'Settings impacting performance can be found under the General Preferences (e.g., maximum undo levels, shadow files, render preview quality) and Produce Preferences (e.g., fast video rendering technology options).',
            'Media Cache': 'Accessed by clicking the Preferences button and selecting the Media Cache tab. Allows you to automatically delete temporary files or manage storage space for downloaded media files.',
            'File Preferences': 'Shows the last folder from which media was imported. You can browse and select a new default import folder. Similarly, the export folder sets where captured media is saved.',
            'Capture Preferences': 'The sources don\'t directly reference "Capture Preferences", but import methods and file formats are detailed.',
            'Slideshow Designer': 'The Slideshow Designer is used for creating slideshows with various image transition effects and customizable settings.',
            'MultiCam Designer': 'The MultiCam Designer is implied to be used for multi-camera editing and synchronizing audio in clips, though no detailed description of its interface is provided.',
            'Action Camera Center': None,
            'Ad Designer': 'The provided sources do not contain any relevant information about "Ad Designer".',
            'Video Editing (General)': 'CyberLink PowerDirector\'s Edit module is where you can perform various video editing tasks. This includes editing and trimming imported media, arranging it in your video production, and adding effects, titles, PiP objects, transitions, music, and subtitles. The editing workspace is where you create your project by adding media, various effects, transitions, and title effects. All of PowerDirector\'s features are available in the Full (Timeline) Mode, which allows you to view your entire project based on running time and see all tracks, media, and other content.',
            'Audio Editing': 'You can edit audio in your video production in PowerDirector\'s Audio Editor. To access it, select an audio or video clip (with audio) on the timeline, click the Tools button above the timeline, and then select Audio Editor. In the Audio Editor, you can decide whether to apply edits to all available channels or only one. You can also use range selection to edit a specific portion of the audio, or skip this step to edit the entire clip.',
            '360° Video Editing': 'The provided sources do not contain any relevant information about "360° Video Editing".',
            'Add Text Overlay': 'To add text to a template within the Video Intro/Outro Designer, click the "Add Text" button and then select Add Text to add a text box. You can then double-click to edit the text and use available options to change font, color, size, and weight.',
            'Add Date/Time/Remark Stamp': 'The provided sources do not contain any relevant information about directly adding "Date/Time/Remark Stamp". However, you can add Timeline Markers and include a Comment field for notes.',
            'Content Aware Editing': 'The provided sources do not contain a direct feature named "Content Aware Editing". However, related features that leverage content analysis include Speech to Text, Body Effects, and Smart Fit for Duration.',
            'Pan & Zoom (for images)': 'CyberLink PowerDirector allows you to add pans and zooms to images, creating a motion effect in your final video. You can select from predefined templates for each image or use the Motion Designer to customize the motion to your liking.',
            'Magic Tools': 'The provided sources do not contain a specific section titled "Magic Tools". However, the section "Using the Tools" lists various editing tools available in CyberLink PowerDirector.',
            'Color Board': 'Color boards allow you to insert solid frames of color into your video. They are useful as quick transitions between video clips or as a background for titles and ending credits.',
            'White Balance': 'White Balance is an option available under the Fixes section when applying fixes and enhancements to media clips. The White calibration option allows you to use an eyedropper to select an area in the video or image that should be white.',
            'Color Temperature': 'Color Temperature is an option available under the White Balance fix when applying fixes and enhancements to media clips. It adjusts the clip\'s color temperature or creates a specific atmosphere (e.g., winter or summer).',
            'Tint': 'Tint is a slider available under the White Balance fix when applying fixes and enhancements to media clips. Use the Tint slider to adjust the color level of the clip.',
            'Background Media Adjustment Settings': 'In the Video Intro/Outro Designer, you can replace the background media of a template and adjust its settings. You can replace the background video/photo with an imported media file from your hard drive, a color board, or media downloaded from Getty Images.',
            'LUTS (Color Filters)': 'LUTs (color look-up tables) are used to transform the range of colors in a video clip to another range. You can find LUTs in the Effect Room under the Color LUT tag. You can also search for and download LUTs in various formats and import them into PowerDirector.',
            'Lens Correction': 'Lens Correction is an option available under the Fixes section when applying fixes and enhancements to media clips. It allows you to auto-correct distorted images/videos using lens profiles.',
            'Brightness, Hue, Saturation, Contrast, Sharpness (Adjust Video)': 'These adjustments are available under the Color Adjustment option within the Enhance section of the Fix/Enhance feature for media clips. These settings can be applied for the entire duration of a clip or customized using keyframes.',
            'Object Grouping/Ungrouping': 'On the timeline, you can group multiple selected media clips by holding down the Shift key and selecting multiple clips. To undo, select Ungroup Objects.',
            'Add Clip Marker': 'You can add clip markers to a selected video/audio clip in the Library Preview Window or directly in the timeline. Use the player controls to find the moment/time position in the clip for the marker and click the "Add Clip Marker" button.',
            'Add Music Beat Marker': 'The provided sources do not contain any relevant information about directly adding "Music Beat Marker".',
            'Edit Clip Marker': 'Once clip markers are added to the timeline, you can modify them by selecting the keyframe and changing the clip\'s properties, or by dragging the keyframe to another position on the timeline.',
            'Remove Selected Clip Marker': 'To remove a keyframe (which clip markers are a type of), select it on the timeline and click the "Remove Keyframe" button.',
            'Remove All Clip Markers': 'The provided sources do not contain any relevant information about removing all clip markers at once.',
            'Snap to:': 'CyberLink PowerDirector includes "snap to" features to aid in precise placement. Clips will snap to other clips on the timeline for easy placement.',
            'Timeline Zoom': 'You can resize the timeline ruler for a more expanded or condensed view of your production. Click the "View Entire Video" button to auto-fit your current project in the timeline area.',
            'Viewer Zoom': 'In the Title Designer, you can use the zoom tools to zoom out and in on the preview window when modifying the title effect.',
            'Full Screen': 'You can view your library or project preview at full screen by clicking the full screen button on an undocked window. To exit full screen mode, press the Esc key on your keyboard.',
            'Timecode Mode': 'While the source doesn\'t explicitly refer to a "Timecode Mode", you can enter a specific timecode in the time field (in the preview player controls) and press Enter to quickly find a specific scene.',
            'Clip Mode': 'When modifying a video style effect, the Effect Settings panel can open in "Clip Mode". In Clip Mode, any changes you make to the effect\'s settings are applied for the entire duration of the effect.',
            'Movie Mode': 'The provided sources do not contain any relevant information about "Movie Mode".',
            'Previous/Next Frame': 'You can use the "Previous Frame" and "Next Frame" buttons in the Preview Player Controls to go to the previous or next frame respectively.',
            'Go to Previous/Next Second': 'The provided sources do not contain any relevant information about directly "Go to Previous/Next Second". However, you can jump to specific timecodes using the time field.',
            'Go to beginning/end of clip/project': 'In the Editing Preferences, there is an option to "Return to beginning of video after preview".',
            'Mark In/Out': 'The "Mark In" and "Mark Out" functions are used for trimming clips and setting ranges. Performing a Single Trim in the Library Preview Window allows you to adjust the position of the clip and set the desired start and end points.',
            'Precut Tool': 'The provided sources mention "Precutting Video Clips" as one of the ways videos can be cut/trimmed into smaller segments or files.',
            'Scene Detection Tool': 'The provided sources do not contain any relevant information about "Scene Detection Tool".',
            'Video Stabilizer': 'Video Stabilizer is an option available under the Fixes section when applying fixes and enhancements to media clips. It employs motion compensation technology to correct shaking videos.',
            'Video Denoise': 'Video Denoise is an option available under the Fixes section when applying fixes and enhancements to media clips. This tool removes video noise from a video clip, including High-ISO and TV signal noise.',
            'Edge Enhancement': 'Edge Enhancement is listed as an enhancement option under "Enhancing Media Clips". The HDR (high dynamic range) effect adjusts the lighting range on the edges in the video image.',
            'Video Upscale': 'The provided sources do not contain any relevant information about "Video Upscale".',
            'Fill Type (for Titles/Borders)': 'For Text Backdrop, Font Face, and Border, Fill Type determines the color and texture. You can choose Solid Color, 2 Color Gradient, or Image for each.',
            'Border Type (for Titles/Borders)': 'You can customize the border\'s Size (thickness), Blur, and Opacity. You can set the Fill Type for the border to Solid Color or Color Gradient.',
            'Crop/Zoom/Pan': 'These are distinct but related editing functions. You can crop video clips or images, zoom in or out, and apply pans to videos and images.',
            'Add freeze frame': 'The provided sources do not contain any relevant information about directly adding "freeze frame".',
            'Add text': 'You can add text in several contexts including Video Intro/Outro Designer, Title Room, and Title Designer.',
            'Flip horizontally/vertically': 'You can flip background media, PiP images, and overlays in a video intro/outro template horizontally or vertically.',
            'Bring Forward/Send Backward': 'You can adjust the layer order of objects within a template, such as title text, PiP images, and video overlays.',
            'Duplicate': 'You can quickly duplicate existing objects in your templates including text, images, and overlays.',
            'Customize Toolbar': 'The provided sources do not contain any relevant information about directly customizing the toolbar.',
            'PowerDirector Hotkeys': 'CyberLink PowerDirector includes a number of keyboard shortcuts (hotkeys) that can make the video editing process quicker and smoother.',
            'Credit': None,
            'AI Copilot': None,
            'Talking Avatar': None,
            'AI Image Generator': None,
            'AI Video Generator': None,
            'AI Video Enhancement': {
                'Lighting Adjustment': 'brightness/contrast/saturation, extreme backlight.',
                'White Balance': 'color temperature, tint, white calibration.',
                'Video Stabilizer': 'corrects shaking videos, fixes rotational camera shake, enhanced stabilizer option.',
                'Lens Correction': 'auto-corrects distorted images/videos using lens profiles, manual fisheye distortion, vignette removal.',
                'Video Denoise': 'removes high-ISO and TV signal noise.',
                'Audio Denoise': 'Uses CLNR (CyberLink Noise Reduction) technology to improve audio quality and reduce background noise.',
                'Wind Removal': 'Removes low-frequency noise caused by wind contacting a microphone. This feature requires macOS 10.15 or above.',
                'Color Adjustment': 'exposure, brightness, contrast, hue, saturation, vibrancy, highlight healing, shadow, sharpness.',
                'Color Enhancement': 'dynamically adjusts color saturation without affecting skin tones.',
                'Color Match': 'matches the color of a selected video or image to another clip in your project.',
                'Split Toning': 'produces creative color effects by adjusting highlight/shadow hues and saturations.',
                'HDR Effect': 'adjusts lighting range on edges, recovers detail, adds dramatic tone.',
                'Speech Enhancement': 'Improves dialogue by isolating it and removing non-stationary background audio/noise.'
            },
            'AI Voice Translator': None,
            'AI Face Blur': 'The Motion Tracker tool can be used to track objects and apply mosaic, spotlight, or blur effects. If a face is tracked as an object, a mosaic or Gaussian blur effect could be applied.',
            'AI Body Effects': 'Uses AI engine to select the most prominent object (people, pets, etc.) and apply selected effects. Effects like Aura, Energy Dots, Lightning, and more are available with customizable properties such as size, color, speed, opacity.',
            'AI Sticker Maker': None,
            'AI Voice Changer': 'The Vocal Transformer effect in the Audio Editor adjusts voice pitch and timbre. Presets like "Robot voice" and "Duck voice" can be used as starting points.',
            'AI Background Remover': 'No specific "AI Background Remover" found. Chroma Key (Green Screen Effect) is available in the PiP Designer to replace a selected color with transparency.',
            'AI Anime Video Effect': None,
            'AI Sky Replacement': None,
            'Video Intro/Outro Designer': {
                'Opening the Designer': 'Right-click a template in the Video Intro/Outro Room and select "Edit in the Video Intro/Outro Designer" or drag a template to the timeline.',
                'Change Template Duration': 'Adjust the overall length of the template (increase by 50% or as short as 5 seconds).',
                'Replace Background Media': 'Replace with a color board, imported media, or Getty Images media.',
                'Crop Background Media Clips': 'Remove unwanted portions of the background video or photo.',
                'Add and Edit Text': 'Edit existing title text or add new text boxes. Customize font, color, size, weight, position, rotation, and more.',
                'Add and Edit Images': 'Add PiP images and color boards. Customize imported color boards and replace existing images.',
                'Add Video Overlays': 'Add PiP objects from the Video Overlay Room. Adjust settings like opacity, border, shadow.',
                'Edit Background Music': 'Import your own music or download from Meta. Use a trim box to select a segment and add fade-in/fade-out.',
                'Saving, Sharing, and Advanced Editing': 'Save, share, or import templates into the main workspace for advanced editing.'
            },
            'Title Designer': {
                'Zoom Tools': 'Zoom in/out on the preview window, set viewer zoom amount, or fit the title effect to the viewer window.',
                'Adding Additional Title Text': 'Click "Add Text" to add a text box in the preview window.',
                'Modifying Title Effect Position, Size, and Orientation': 'Drag title text/images to new positions, resize, and rotate titles.',
                'Saving and Sharing Title Templates': 'Save templates, upload to DirectorZone, or back up to CyberLink Cloud.',
                'Modifying Titles in Express Mode': 'Focuses on Text Properties such as font, size, spacing, and custom presets.',
                'Modifying Titles in Advanced Mode': 'Complete customization including adding images, particles, backgrounds, and animations.'
            },
            'Particle Designer': 'No information found on a specific "Particle Designer". Particle effects are added from the Particle Room and can be inserted and customized within the Title Designer.',
            'Sketch Designer': None,
            'Shape Designer': 'Allows creation and customization of shapes using keyframes. Shapes are treated as PiP objects.',
            'Creation': None,
            'AI Music Generator': None,
            'Text to Video': None,
            'Image to Video': None,
            'Speech to Text': None,
            'Text + Face': None,
            'Improvement Program': None,
            'AI Sound Generator': None,
        },
        "guidedline": [
            "Analyze the string: Review the string to identify the relevant 'classification' information from the dictionary.",
            "Find the corresponding key: Locate the dictionary key in the 'classification' that best matches the description.",
            "Return the key name: Provide the dictionary key from 'classification' that corresponds to the string."
        ],
        "Note": [
            "Classify the string based on the provided information.",
            "Consider the context and meaning of the string when classifying.",
            "Review the classification carefully; avoid relying solely on previous classifications.",
            "If no match is found, return 'No Matched'."
        ]
    }

    # Convert to JSON string
    return json.dumps(system_prompt, ensure_ascii=False, indent=2)

def prompt(source_string):
    # Create the JSON prompt structure
    prompt = {
        "Input": source_string,
        "Output": "Classifcation Name (ENU) Only"
    }
    
    # Convert to JSON string
    return json.dumps(prompt, ensure_ascii=False, indent=2)

def read_json(json_path):
    # Read the JSON file
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)

    if not data:
        print("Warning: Empty JSON data")
        return None
    return data
    

async def get_classification(data, output_path=None):
    model_name = conf.TRANSLATE_MODEL

    if 'o3' in model_name:
        kwargs = {}
    else:
        kwargs = {"temperature": conf.TEMPERATURE}
    if conf.SEED is not None:
        kwargs["seed"] = conf.SEED


    chat = OpenaiAPIChat(
        model_name=model_name,
        system_prompt= system_prompt(),
    )

    # print('=====System Prompt=====')
    # print(chat.sys_prompt)
    # print('=====System Prompt=====')

    for key, value in data.items():
        try:
            source_str = value[0]
            translated_str = value[1]
            p = prompt(source_str)
            # print('=====Prompt=====')
            # print(p)
            # print('=====Prompt=====')

            response = ''
            stop_reason = ''
            print(f"key {key}, source str: {source_str}")

            try:
                async for chunk, review_stop_reason in chat.get_stream_aresponse(p, **kwargs):
                    response += chunk
                    stop_reason = review_stop_reason
                    
                if stop_reason == 'length':
                    print("Review response exceeded length limit but received partial content.")
                    raise RuntimeError("Review response too short after hitting length limit.")
                
            except RuntimeError as e:
                print(f"Review process failed: {str(e)}")
                raise RuntimeError("Translation review failed due to length limit or other issues.")
            
            print(f"Review response: {response}")
            # print(type(response))

            # Save result to excel with format key/ source/ translated/ classification
            result = {
                "key": key,
                "source": source_str,
                "translated": translated_str,
                "classification": response
            }

            # Save to excel
            # Create a list to store results
            results = []
            results.append(result)

            # Create DataFrame from results list
            if not output_path:
                output_path = "classification_results.xlsx"

            # Check if we have a static DataFrame attribute already
            if not hasattr(get_classification, 'df'):
                try:
                    # Try to read existing file
                    get_classification.df = pd.read_excel(output_path, engine='openpyxl')
                except (FileNotFoundError, pd.errors.EmptyDataError):
                    # Create new DataFrame if file doesn't exist
                    get_classification.df = pd.DataFrame(columns=["key", "source", "translated", "classification"])

            # Append the new result to the DataFrame
            get_classification.df = pd.concat([get_classification.df, pd.DataFrame([result])], ignore_index=True)

            # Save the updated DataFrame to Excel
            get_classification.df.to_excel(output_path, index=False, engine='openpyxl')
            # print(f"Classification result appended to {output_path}")

            # copy output_file for backup
            # Create a backup of the output file

            if int(key)%10 ==0:
                # Generate backup filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = output_path.replace(".xlsx", f"_backup_{timestamp}.xlsx")
                backup_path = backup_path.replace("database", "database/backup")

                # Copy the file
                try:
                    shutil.copy2(output_path, backup_path)
                    print(f"Created backup at: {backup_path}")
                except Exception as backup_err:
                    print(f"Warning: Could not create backup: {backup_err}")

        except Exception as e:
            print(f"Error processing key {key}: {e}")
            # Save result to excel with format key/ source/ translated/ classification
            result = {
                "key": key,
                "source": source_str,
                "translated": f"Error processing key {key}: {e}",
                "classification": 'Error processing'
            }

            # Save to excel
            # Create a list to store results
            results = []
            results.append(result)

            # Create DataFrame from results list
            if not output_path:
                output_path = "classification_results.xlsx"

            # Check if we have a static DataFrame attribute already
            if not hasattr(get_classification, 'df'):
                try:
                    # Try to read existing file
                    get_classification.df = pd.read_excel(output_path, engine='openpyxl')
                except (FileNotFoundError, pd.errors.EmptyDataError):
                    # Create new DataFrame if file doesn't exist
                    get_classification.df = pd.DataFrame(columns=["key", "source", "translated", "classification"])

            # Append the new result to the DataFrame
            get_classification.df = pd.concat([get_classification.df, pd.DataFrame([result])], ignore_index=True)

            # Save the updated DataFrame to Excel
            get_classification.df.to_excel(output_path, index=False, engine='openpyxl')
            # print(f"Classification result appended to {output_path}")
            continue

async def process_segments(data, output_path):
        result = await get_classification(data, output_path)
        return result

def pre_process_data(data, output_path):
# read output path by pandas
    try:
        df_existing = pd.read_excel(output_path, engine='openpyxl')
        # Initialize the static DataFrame with existing data
        get_classification.df = df_existing
        print(f"Loaded existing classification data from {output_path}")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        # If file doesn't exist or is empty, create a new DataFrame
        get_classification.df = pd.DataFrame(columns=["key", "source", "translated", "classification"])
        print(f"Creating new classification data file at {output_path}")

    segments_to_process = {}
    
    # Identify which keys are not yet processed
    processed_sources = list(set(get_classification.df['source'].tolist()))

    
    # Add unprocessed segments to the processing list
    for key, value in data.items():
        if value[0] not in processed_sources:
            segments_to_process[key] = value
    
    print(f"Found {len(segments_to_process)} new segments to process")

    # Remove duplicate source strings, keeping only one occurrence of each
    unique_sources = set()
    unique_segments = {}
    
    for key, value in segments_to_process.items():
        source_str = value[0]
        if source_str not in unique_sources:
            unique_sources.add(source_str)
            unique_segments[key] = value
    
    # Replace the original dictionary with the deduplicated version
    segments_to_process = unique_segments
    
    print(f"After removing duplicates: {len(segments_to_process)} segments to process")
    # Print the top 5 segments to process (if available)
    if segments_to_process:
        print("Top 5 segments to be processed:")
        for i, (key, value) in enumerate(list(segments_to_process.items())[:5]):
            print(f"{i+1}. Key: {key}")
            print(f"   Source: {value[0][:100]}..." if len(value[0]) > 100 else f"   Source: {value[0]}")
            print(f"   Translation: {value[1][:100]}..." if len(value[1]) > 100 else f"   Translation: {value[1]}")
            print("-" * 50)

    return segments_to_process
def compare_result(json_path, output_path) -> None:
    data = read_json(json_path)
    if not data:
        print("No data to process.")
        return
    segments_to_process = pre_process_data(data, output_path)
    
    if segments_to_process:
        try:
            # Use a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the async processing function
            results = loop.run_until_complete(
                process_segments(segments_to_process, output_path))
            
            # Close the event loop
            loop.close()
            
        except Exception as e:
            print(f"Error during classification: {e}")
    else:
        print("No new segments to process")


if __name__ == "__main__":
    json_path = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v11\database\To_class_string.txt"
    output_path = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v11\database\classification_results.xlsx"
    # Example source string to classify
    compare_result(json_path, output_path)

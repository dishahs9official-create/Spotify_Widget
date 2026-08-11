import asyncio
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winrt.windows.storage.streams import DataReader, Buffer, InputStreamOptions
import io
from PIL import Image

async def main():
    manager = await MediaManager.request_async()
    session = manager.get_current_session()
    
    if not session:
        print("No active media session.")
        return
        
    print(f"App: {session.source_app_user_model_id}")
    props = await session.try_get_media_properties_async()
    print(f"Title: {props.title}")
    print(f"Artist: {props.artist}")
    print(f"Has thumbnail: {props.thumbnail is not None}")
    
    if props.thumbnail:
        try:
            print("Opening thumbnail read stream...")
            stream = await props.thumbnail.open_read_async()
            size = stream.size
            print(f"Stream size: {size}")
            
            buffer = Buffer(size)
            await stream.read_async(buffer, size, InputStreamOptions.READ_AHEAD)
            print(f"Read buffer length: {buffer.length}")
            
            reader = DataReader.from_buffer(buffer)
            byte_data = bytearray(buffer.length)
            reader.read_bytes(byte_data)
            print(f"Bytes read successfully: {len(byte_data)}")
            
            # Try to open with Pillow
            img = Image.open(io.BytesIO(byte_data))
            print(f"Pillow Image opened! Format: {img.format}, Size: {img.size}")
            img.save("test_thumbnail_success.png")
            print("Saved image to test_thumbnail_success.png!")
        except Exception as e:
            print(f"Exception reading thumbnail: {e}")

if __name__ == "__main__":
    asyncio.run(main())

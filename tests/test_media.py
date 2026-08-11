import asyncio
from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winrt.windows.storage.streams import DataReader, Buffer, InputStreamOptions
import io
from PIL import Image

async def main():
    print("Requesting media manager...")
    manager = await MediaManager.request_async()
    session = manager.get_current_session()
    
    if not session:
        print("No active media session found. Please play some music first!")
        return
        
    print(f"Active session app: {session.source_app_user_model_id}")
    
    # Get media properties
    props = await session.try_get_media_properties_async()
    print(f"Title: {props.title}")
    print(f"Artist: {props.artist}")
    print(f"Album: {props.album_title}")
    
    # Save thumbnail
    if props.thumbnail:
        print("Thumbnail found, trying to read...")
        stream = await props.thumbnail.open_read_async()
        size = stream.size
        print(f"Thumbnail size: {size} bytes")
        
        buffer = Buffer(size)
        await stream.read_async(buffer, size, InputStreamOptions.READ_AHEAD)
        
        reader = DataReader.from_buffer(buffer)
        byte_data = reader.read_bytes(buffer.length)
        
        img = Image.open(io.BytesIO(bytearray(byte_data)))
        img.save("test_thumb.jpg")
        print("Thumbnail saved to test_thumb.jpg!")
    else:
        print("No thumbnail found.")

if __name__ == "__main__":
    asyncio.run(main())

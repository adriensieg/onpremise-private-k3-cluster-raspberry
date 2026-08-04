// Plays back streamed Float32 PCM audio chunks received from Gemini.
class PCMProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.buffer = new Float32Array();

        this.port.onmessage = (e) => {
            const newData = e.data;
            const merged = new Float32Array(this.buffer.length + newData.length);
            merged.set(this.buffer);
            merged.set(newData, this.buffer.length);
            this.buffer = merged;
        };
    }

    process(inputs, outputs) {
        const channel = outputs[0][0];
        if (!channel) return true;

        if (this.buffer.length >= channel.length) {
            channel.set(this.buffer.slice(0, channel.length));
            this.buffer = this.buffer.slice(channel.length);
        } else {
            // Not enough buffered audio yet — output silence for this frame.
            channel.fill(0);
        }
        return true;
    }
}

registerProcessor('pcm-processor', PCMProcessor);
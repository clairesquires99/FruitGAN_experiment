<script>
	let frame_num = 20;
	function imported_function(frame_num) {
		fecth("./test");
		// .then((d) => d.text())
		// .then((d) => (frame_num = d));
	}
</script>

<img
	src="images/iteration-02_frame-{String(frame_num).padStart(3, '0')}.png"
	alt="experimental fruit"
/>

<label>
	<input type="range" bind:value={frame_num} min="0" max="39" />
</label>
<p>Slider is at {frame_num}</p>
<button on:click={() => imported_function(frame_num)}>Confirm</button>

<style>
	label {
		display: flex;
	}
	input,
	p {
		margin: 6px;
	}
</style>

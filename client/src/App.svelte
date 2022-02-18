<script>
	let frame_num = 20;
	let sessionID = -1;
	function doSomething() {
		fecth("./getSessionID")
			.then((d) => d.text())
			.then((d) => (sessionID = d));
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
<p>This is your session ID: {sessionID}</p>
<button on:click={doSomething}>Confirm</button>

<style>
	label {
		display: flex;
	}
	input,
	p {
		margin: 6px;
	}
</style>

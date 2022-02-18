<script>
	let frame_num = 20;
	let start_experiment = () => {
		fetch("./start_experiment");
	};
	let run_experiment = (arg) => {
		fetch("./running_experiment/" + arg);
	};
</script>

<button on:click={start_experiment()}>Start experiment</button>
<p />
<img
	src="images/frame-{String(frame_num).padStart(3, '0')}.png"
	alt="experimental fruit"
/>

<label>
	<input type="range" bind:value={frame_num} min="0" max="39" />
</label>
<p>Slider is at {frame_num}</p>
<button on:click={run_experiment(frame_num)}>Confirm</button>

<style>
	label {
		display: flex;
	}
	input,
	p {
		margin: 6px;
	}
</style>

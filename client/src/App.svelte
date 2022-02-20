<script>
	import { onMount } from "svelte";

	let frame_num = 20;
	let iter_num = 0;
	let tot_iterations = -1;

	onMount(async () => {
		fetch("./start_experiment")
			.then((d) => d.text())
			.then((d) => (tot_iterations = d));
	});

	let run_experiment = (arg) => {
		if (iter_num < tot_iterations) {
			iter_num++;
			fetch("./running_experiment/" + arg);
		} else {
			fetch("./done");
		}
	};
</script>

<main>
	<img
		src="images/frame-{String(frame_num).padStart(3, '0')}.png"
		alt="experimental fruit"
	/>

	<label>
		<input type="range" bind:value={frame_num} min="0" max="39" />
	</label>
	<p>Slider is at {frame_num}</p>
	<button on:click={run_experiment(frame_num)}>Confirm</button>
	<p>Iteration {iter_num}</p>
	<p>Total iterations {tot_iterations}</p>
</main>

<style>
	label {
		display: flex;
	}
	input,
	p {
		margin: 6px;
	}
</style>

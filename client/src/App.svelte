<script>
	import { onMount } from "svelte";
	import { Moon } from "svelte-loading-spinners";

	let frame_num = 20;
	let iter_num = 0;
	let tot_iterations;
	let response;
	let response2;

	onMount(() => {
		response = fetch("./start_experiment")
			.then((d) => d.text())
			.then((d) => (tot_iterations = d));
	});

	let run_experiment = (arg) => {
		if (iter_num < tot_iterations) {
			iter_num++;
			response = fetch("./running_experiment/" + arg);
		} else {
			fetch("./done");
			// this.redirect(302, "./done");
		}
	};
</script>

<main>
	{#await response}
		<p>Loading...</p>
		<Moon size="60" color="#FF3E00" unit="px" duration="1s" />
	{:then}
		{#if response}
			<img
				src="images/iteration-{String(iter_num).padStart(2, '0')}_
				frame-{String(frame_num).padStart(3, '0')}.png"
				alt="experimental fruit"
			/>
		{/if}
	{/await}

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

<script>
	import { onMount } from "svelte";
	import { Moon } from "svelte-loading-spinners";

	let frame_num = 20;
	let iter_num = 0;
	let tot_iterations;
	let response;
	let target_category = "loading..."; //place holder
	let session_ID;

	onMount(() => {
		response = fetch("./start_experiment")
			.then((data) => data.json())
			.then((data) => {
				tot_iterations = data.tot_iterations;
				session_ID = data.session_ID;
				target_category = data.target_category;
			});
	});

	let run_experiment = (arg) => {
		if (iter_num < tot_iterations) {
			iter_num++;
			response = fetch("./running_experiment/" + arg);
		} else {
			window.location.href = "./done";
		}
	};
</script>

<div class="container-lg d-flex justify-content-center">
	<div class="container-md cont">
		<div class="cont-fruit-image">
			{#await response}
				<Moon size="60" color="#333" unit="px" duration="1s" />
			{:then}
				{#if response}
					<img
						src="images/iteration-{String(iter_num).padStart(2, '0')}_
				frame-{String(frame_num).padStart(3, '0')}.png"
						alt="experimental fruit"
					/>
				{/if}
			{/await}
		</div>

		<p>
			Adjust the slider to match the following <br />word as well as possible:
		</p>
		<p><strong>{target_category}</strong></p>
		<input
			class="form-range"
			type="range"
			bind:value={frame_num}
			min="0"
			max="39"
		/>
		<p class="small text-muted">Slider is at {frame_num}</p>
		<button class="btn btn-primary" on:click={run_experiment(frame_num)}
			>Confirm</button
		>
		<p class="small text-muted">Iteration: {iter_num}</p>
		<p class="small text-muted">Total iterations: {tot_iterations}</p>
		<p class="small text-muted">Session ID: {session_ID}</p>
	</div>
</div>

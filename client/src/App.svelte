<script>
	import { onMount } from "svelte";
	import { Moon } from "svelte-loading-spinners";

	let exp_num;
	let tot_experiments;
	let chain_num;
	let tot_chains;
	let iter_num = 0;
	let tot_iterations;
	let response;
	let target_category = "loading..."; //place holder
	let session_ID;
	let tot_frames;
	let expected_tot_frames = 99; // randomise slider position
	let frame_num = 0; //initialise slider position

	async function start_experiment() {
		return fetch(`./start_experiment?session_ID=${session_ID}`)
			.then((data) => data.json())
			.then((data) => {
				session_ID = data.session_ID;
				exp_num = data.exp_num;
				chain_num = data.chain_num;
				iter_num = data.iter_num;
				tot_iterations = data.tot_iterations;
				target_category = data.target_category;
				tot_frames = data.tot_frames;
			});
	}

	onMount(async () => {
		await fetch("./get_ID")
			.then((data) => data.json())
			.then((data) => {
				session_ID = data.session_ID;
				exp_num = data.exp_num;
				tot_experiments = data.tot_experiments;
				target_category = data.target_category;
				tot_chains = data.tot_chains;
				chain_num = data.chain_num;
			});
		response = start_experiment();
		frame_num = Math.floor(expected_tot_frames / 2);
	});

	async function run_experiment(arg) {
		if (exp_num < tot_experiments) {
			if (iter_num < tot_iterations) {
				response = fetch(
					`./running_experiment?session_ID=${session_ID}&selected_frame=${arg}`
				)
					.then((data) => data.json())
					.then((data) => {
						session_ID = data.session_ID;
						exp_num = data.exp_num;
						iter_num = data.iter_num;
						tot_frames = data.tot_frames;
						chain_num = data.chain_num;
					});
				frame_num = Math.floor(Math.random() * expected_tot_frames);
			} else {
				await fetch(`./end_chain?session_ID=${session_ID}`)
					.then((data) => data.json())
					.then((data) => {
						session_ID = data.session_ID;
						exp_num = data.exp_num;
						target_category = data.target_category;
						tot_chains = data.tot_chains;
						chain_num = data.chain_num;
						iter_num = 0; //stops the progress bar jumping
					});

				if (exp_num == tot_experiments) {
					window.location.href = `./done?session_ID=${session_ID}`;
				} else {
					// start the next experiment
					response = start_experiment();
					frame_num = Math.floor(expected_tot_frames / 2);
				}
			}
		}
	}
</script>

<div class="container-lg d-flex justify-content-center">
	<div class="container-md cont">
		<div class="alert-cont">
			{#await response then}
				{#if iter_num == 0 && exp_num != 0}
					<div class="alert alert-primary" role="alert">
						Warning: the word changed!
					</div>
				{/if}
			{/await}
		</div>

		<div class="cont-fruit-image">
			{#await response}
				<Moon size="60" color="#333" unit="px" duration="1s" />
			{:then}
				{#if response}
					<img
						src="images/{session_ID}/{target_category}{chain_num}/
						iteration-{String(iter_num).padStart(2, '0')}_
						frame-{String(frame_num).padStart(3, '0')}.png"
						alt="experimental fruit"
					/>
				{/if}
			{:catch error}
				<div class="alert alert-danger" role="alert">
					Oops, something went wrong.
				</div>
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
			max={tot_frames}
		/>
		<p class="small text-muted">Slider is at {frame_num}</p>
		<button class="btn btn-primary" on:click={run_experiment(frame_num)}
			>Confirm</button
		>
		<p class="small text-muted">Iteration: {iter_num} / {tot_iterations}</p>
		<p class="small text-muted">Chain number: {chain_num} / {tot_chains}</p>
		<p class="small text-muted">Exp number: {exp_num} / {tot_experiments}</p>
		<br />
		<p class="small text-muted">Session ID: {session_ID}</p>
		<div class="progress mt-5">
			<div
				class="progress-bar progress-bar-striped"
				role="progressbar"
				style="width: {((exp_num * tot_iterations + iter_num) /
					(tot_experiments * tot_iterations)) *
					100}%"
				aria-valuenow={iter_num}
				aria-valuemin="0"
				aria-valuemax={tot_iterations}
			/>
		</div>
	</div>
</div>

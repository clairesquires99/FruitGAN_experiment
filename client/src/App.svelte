<script>
	import { onMount } from "svelte";
	import { Moon } from "svelte-loading-spinners";

	let chain_num;
	let tot_chains;
	let iter_num = 0;
	let tot_iterations;
	let response;
	let target_category = "loading..."; //place holder
	let session_ID;
	let tot_frames = 99;
	let expected_tot_frames = 99; // randomise slider position
	let frame_num = 0; //initialise slider position

	async function setup() {
		return fetch("./start_experiment")
			.then((data) => data.json())
			.then((data) => {
				session_ID = data.session_ID;
				target_category = data.target_category;
				tot_chains = data.tot_chains;
				chain_num = data.chain_num;
			});
	}
	async function start_chain(arg) {
		frame_num = Math.floor(expected_tot_frames / 2);
		return fetch(`./start_chain?session_ID=${session_ID}&chain_num=${arg}`)
			.then((data) => data.json())
			.then((data) => {
				iter_num = data.iter_num;
			});
	}

	async function run_chain(arg) {
		return fetch(
			`./run_chain?session_ID=${session_ID}&chain_num=${chain_num}&selected_frame=${arg}`
		)
			.then((data) => data.json())
			.then((data) => {
				session_ID = data.session_ID;
				iter_num = data.iter_num;
				chain_num = data.chain_num;
			});
	}

	async function end_chain(arg) {
		return fetch(`./end_chain?session_ID=${session_ID}&chain_num=${arg}`)
			.then((data) => data.json())
			.then((data) => {
				session_ID = data.session_ID;
				iter_num = data.iter_num;
				tot_frames = data.tot_frames;
				chain_num = data.chain_num;
			});
	}

	onMount(async () => {
		await setup();
		response = start_chain(0);
		start_chain(1);
		start_chain(2);
	});

	function run_experiment(arg) {
		if (iter_num < tot_iterations) {
			run_chain(arg);
		}

		if (iter_num == tot_iterations) {
			end_chain(0);
			end_chain(1);
			end_chain(2);
			window.location.href = `./done?session_ID=${session_ID}`;
		}
	}
</script>

<div class="container-lg d-flex justify-content-center">
	<div class="container-md cont">
		<div class="cont-fruit-image">
			{#await response}
				<Moon size="60" color="#333" unit="px" duration="1s" />
			{:then}
				{#if response}
					<img
						src="images/{session_ID}/{target_category}{chain_num - 1}/
						iteration-{String(iter_num).padStart(2, '0')}_
						frame-{String(frame_num).padStart(3, '0')}.png"
						alt="experimental fruit"
					/>
				{/if}
			{:catch error}
				<div class="alert alert-danger" role="alert">
					Oops, something went wrong. <br /> Please close the tab and try again.
					<br /> If the error persists, contact s1843530@ed.ac.uk.<br />
					{error.message}
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
		<!-- <p class="small text-muted">Slider is at {frame_num}</p> -->
		<br />
		<button class="btn btn-primary m-3" on:click={run_experiment(frame_num)}
			>Confirm</button
		>
		<p class="small text-muted">Iteration: {iter_num} / {tot_iterations}</p>
		<p class="small text-muted">Chain number: {chain_num} / {tot_chains}</p>
		<br />
		<!-- <div class="progress mt-5">
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
		</div> -->
		<p class="small text-muted">Session ID: {session_ID}</p>
	</div>
</div>

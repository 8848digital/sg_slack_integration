frappe.pages["knowledge-helper-leaderboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: "Knowledge Helper Leaderboard",
		single_column: true,
	});

	// Create a div for leaderboard
	$(wrapper)
		.find(".layout-main-section")
		.append(`<div id="leaderboard" style="margin-top:20px"></div>`);

	// Fetch data
	frappe.call({
		method: "your_app.slack_event.get_leaderboard",
		callback: function (r) {
			if (r.message) {
				render_leaderboard(r.message);
			}
		},
	});

	function render_leaderboard(data) {
		let html = `<table class="table table-bordered" style="max-width: 600px;">
                        <thead>
                            <tr>
                                <th>Rank</th>
                                <th>User ID</th>
                                <th>Helpful Reactions</th>
                            </tr>
                        </thead>
                        <tbody>`;

		data.forEach((row, index) => {
			html += `<tr>
                        <td>${index + 1}</td>
                        <td>${row.slack_user_id}</td>
                        <td>${row.helpful_count}</td>
                     </tr>`;
		});

		html += `</tbody></table>`;

		$("#leaderboard").html(html);
	}
};

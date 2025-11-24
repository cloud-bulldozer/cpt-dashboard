import * as API_ROUTES from "@/utils/apiConstants";
import * as TYPES from "./types.js";

import API from "@/utils/axiosInstance";

import { getRequestParams } from "./commonActions";

export const fetchOSOJobs = () => async (dispatch) => {
	try {
		dispatch({ type: TYPES.LOADING });

		const params = dispatch(getRequestParams("oso"));

		const response = await API.get(API_ROUTES.OSO_JOBS_API_V1, { params });

		if (response?.data?.results?.length > 0) {
			dispatch({
				type: TYPES.SET_OSO_JOBS_DATA,
				payload: response.data.results,
			});

			dispatch(tableReCalcValues());
			dispatch({
				type: TYPES.SET_OSO_PAGE_TOTAL,
				payload: {
					total: response.data.total,
					offset: response.data.offset,
				},
			});
		}
	} catch (error) {
		console.error(
			`ERROR (${error?.response?.status}): ${JSON.stringify(
				error?.response?.data
			)}`
		);
	}
	dispatch({ type: TYPES.COMPLETED });
};

export const tableReCalcValues = () => (dispatch, getState) => {
	const { page, perPage } = getState().oso;

	dispatch(setOSOPageOptions(page, perPage));
};

export const setOSOPage = (pageNo) => ({
	type: TYPES.SET_OSO_PAGE,
	payload: pageNo,
});

export const setOSOPageOptions = (page, perPage) => ({
	type: TYPES.SET_OSO_PAGE_OPTIONS,
	payload: { page, perPage },
});

export const setOSOOffset = (offset) => ({
	type: TYPES.SET_OSO_OFFSET,
	payload: offset,
});

export const setOSOSortIndex = (index) => ({
	type: TYPES.SET_OSO_SORT_INDEX,
	payload: index,
});

export const setOSOSortDir = (direction) => ({
	type: TYPES.SET_OSO_SORT_DIR,
	payload: direction,
});

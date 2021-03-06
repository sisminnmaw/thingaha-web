import {
  GET_ALL_ADDRESSES_SUCCESS,
  GET_ALL_ADDRESSES_FAILURE,
  GET_SEARCH_ADDRESSES_SUCCESS,
  GET_SEARCH_ADDRESSES_FAILURE,
} from '../actions/addresses'
import { normalizeRecordsById } from '../../utils/reducerHelpers'

export default (state = { addresses: {} }, action) => {
  switch (action.type) {
    case GET_ALL_ADDRESSES_SUCCESS:
      return {
        ...state,
        addresses: normalizeRecordsById(action.addresses),
        totalCount: action.totalCount,
        totalPages: action.totalPages,
        currentPage: action.currentPage,
      }
    case GET_ALL_ADDRESSES_FAILURE:
      return {
        ...state,
        error: action.error,
      }
    case GET_SEARCH_ADDRESSES_SUCCESS:
      return {
        ...state,
        addresses: [...action.addresses],
        count: action.count,
      }
    case GET_SEARCH_ADDRESSES_FAILURE:
      return {
        ...state,
        error: action.error,
      }
    default:
      return state
  }
}

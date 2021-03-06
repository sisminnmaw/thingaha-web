import React, { useState } from 'react'
import styled from 'styled-components'
import DonatorCard from './DonatorCard'
import { connect } from 'react-redux'
import * as actions from '../../store/actions'
import Input from '@material-ui/core/Input'
import InputAdornment from '@material-ui/core/InputAdornment'
import SearchIcon from '@material-ui/icons/Search'
import Typography from '@material-ui/core/Typography'
import Chip from '@material-ui/core/Chip'
import { formatMMK, formatJPY } from '../../utils/formatCurrency'
import { MONTHS } from '../../utils/dateAndTimeHelpers'
import range from 'lodash/range'
import MenuItem from '@material-ui/core/MenuItem'
import ThingahaSelect from '../common/ThingahaSelect'

const DonatorList = styled.ul`
  list-style: none;
  margin: 0;
  padding: 0;

  & li {
    margin-bottom: 0.5rem;
  }
`

const MonthHeading = styled(Typography)`
  & .year {
    color: ${({ theme }) => theme.palette.text.primary};
    font-size: 1.25rem;
  }

  & .month {
    margin-left: 0.5rem;
    color: ${({ theme }) => theme.palette.text.primary};
    font-size: 1.25rem;
  }

  & .current-page-total {
    margin-left: 0.5rem;
  }
`

const HeadingContainer = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
`

const SearchInput = ({ onChange }) => {
  return (
    <Input
      id="input-with-icon-adornment"
      startAdornment={
        <InputAdornment position="start">
          <SearchIcon />
        </InputAdornment>
      }
      onChange={onChange}
    />
  )
}

const Heading = ({
  selectedYear,
  selectedMonth,
  setSelectedYear,
  setSelectedMonth,
  setSearchTerm,
  currentPageTotal,
}) => {
  return (
    <HeadingContainer>
      <MonthHeading component={'span'}>
        <ThingahaSelect
          onChange={(e) => {
            setSelectedYear(e.target.value)
          }}
          value={selectedYear}
          id="year"
          name="year"
          label="year"
          className="year"
        >
          {range(selectedYear - 10, selectedYear + 11, 1).map((year) => {
            return (
              <MenuItem value={year} key={year}>
                {year}
              </MenuItem>
            )
          })}
        </ThingahaSelect>
        <ThingahaSelect
          onChange={(e, newValue) => {
            setSelectedMonth(e.target.value)
          }}
          value={selectedMonth}
          id="month"
          name="month"
          label="month"
          className="month"
        >
          {MONTHS.map((monthData) => {
            return (
              <MenuItem value={monthData.value} key={monthData.value}>
                {monthData.name}
              </MenuItem>
            )
          })}
        </ThingahaSelect>

        <Chip
          label={currentPageTotal}
          variant="default"
          size="small"
          className="current-page-total"
        />
      </MonthHeading>
      <SearchInput
        onChange={(e) => {
          setSearchTerm(e.target.value)
        }}
      />
    </HeadingContainer>
  )
}

const CurrentMonthDonations = ({
  donations,
  updateDonationStatus,
  selectedYear,
  selectedMonth,
  setSelectedYear,
  setSelectedMonth,
}) => {
  const [searchTerm, setSearchTerm] = useState('')

  const handleToggle = (donation) => {
    const newStatus = donation.status === 'pending' ? 'paid' : 'pending'
    updateDonationStatus(donation.id, newStatus)
  }

  let filteredDonations = donations
  if (searchTerm != '') {
    filteredDonations = donations.filter((donation) =>
      donation.user.display_name.toLowerCase().match(searchTerm.toLowerCase())
    )
  }

  return (
    <>
      <Heading
        selectedYear={selectedYear}
        selectedMonth={selectedMonth}
        setSelectedYear={setSelectedYear}
        setSelectedMonth={setSelectedMonth}
        setSearchTerm={setSearchTerm}
        currentPageTotal={filteredDonations.length}
      />
      <DonatorList>
        {filteredDonations.map((donation, index) => {
          return (
            <li key={donation.id}>
              <DonatorCard
                index={index}
                handleToggle={() => handleToggle(donation)}
                checked={donation.status === 'paid'}
                description={donation.user.display_name}
                amount={
                  donation.user.country === 'jp'
                    ? formatJPY(donation.jpy_amount)
                    : formatMMK(donation.mmk_amount)
                }
              />
            </li>
          )
        })}
      </DonatorList>
    </>
  )
}

const mapStateToProps = (state) => ({})

const mapDispatchToProps = (dispatch) => {
  return {
    // dispatching plain actions
    getDonationsForMonth: (year, month) =>
      dispatch(actions.getDonationsForMonth(year, month)),

    updateDonationStatus: (id, status) =>
      dispatch(actions.updateDonationStatus(id, status)),
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(CurrentMonthDonations)

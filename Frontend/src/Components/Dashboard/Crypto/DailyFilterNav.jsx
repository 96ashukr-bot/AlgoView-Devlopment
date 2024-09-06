import React, { useState } from 'react';
import { Nav, NavItem, NavLink } from 'reactstrap';

const DailyFilterNav = () => {
  const dailyFilter = ['1H', '1D', '1W', '1M', '1Y'];
  const [active, setActive] = useState(dailyFilter[0]);
  return (
    <Nav tabs className='custom-tab'>
      {dailyFilter.map((item, i) => (
        <NavItem key={i}>
          <NavLink tag='button' onClick={(e) => setActive(item)} className={`nav-link ${active === item && 'active'}`}>
            {item}
          </NavLink>
        </NavItem>
      ))}
    </Nav>
  );
};

export default DailyFilterNav;

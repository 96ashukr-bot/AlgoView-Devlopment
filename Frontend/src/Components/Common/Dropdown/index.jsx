import React, { useState } from 'react';
import { Dropdown, DropdownItem, DropdownMenu, DropdownToggle } from 'reactstrap';

const DropdownCommon = ({ dropdownMain, icon = true, iconName, btn, options }) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const toggle = () => setDropdownOpen((prevState) => !prevState);

  return (
    <Dropdown {...dropdownMain} isOpen={dropdownOpen} toggle={toggle}>
      <DropdownToggle {...btn}>
        {icon && <i className={iconName}></i>}
        {!icon && options[0]}
      </DropdownToggle>
      <DropdownMenu>
        {options.map((item, i) => (
          <DropdownItem key={i}>{item}</DropdownItem>
        ))}
      </DropdownMenu>
    </Dropdown>
  );
};

export default DropdownCommon;

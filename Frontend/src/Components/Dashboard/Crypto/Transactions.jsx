import React, { useState } from 'react';
import { Card, CardBody, CardHeader, Nav, NavItem } from 'reactstrap';
import { Btn, H5 } from '../../../AbstractElements';
import { TransactionsTitle } from '../../../Constant';
import { transactionTableData } from '../../../Data/Crypto';
import useShowClass from '../../../Hooks/useShowClass';
import TransactionTable from './TransactionTable';

const Transactions = () => {
  const NavTab = ['All', 'Buy', 'Sell'];
  const [active, setActive] = useState('All');
  const [show, setShow] = useShowClass('show');
  const activeHandler = (item) => {
    setActive(item);
    setShow('');
  };

  return (
    <Card className='tranaction-card'>
      <CardHeader className='card-no-border'>
        <div className='header-top'>
          <H5>{TransactionsTitle}</H5>
          <Nav tabs className='custom-tab'>
            {NavTab.map((item, i) => (
              <NavItem key={i}>
                <Btn attrBtn={{ color: 'transparent', onClick: (e) => activeHandler(item), className: `nav-link ${active === item && 'active'}` }}>{item}</Btn>
              </NavItem>
            ))}
          </Nav>
        </div>
      </CardHeader>
      <CardBody className='pt-0'>
        <div className={`fade ${show} table-responsive recent-table transaction-table`}>
          <TransactionTable filterCoins={active} tableData={transactionTableData} />
        </div>
      </CardBody>
    </Card>
  );
};

export default Transactions;

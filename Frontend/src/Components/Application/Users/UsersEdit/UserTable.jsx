import axios from 'axios';
import React, { Fragment, useContext, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader } from 'reactstrap';
import { Btn, H4 } from '../../../../AbstractElements';
import { UserEditTableAPI } from '../../../../api';
import { Delete, Edit, Update, UsersTableHeader, UsersTableTitle } from '../../../../Constant';
import CustomizerContext from '../../../../_helper/Customizer';

const UserTable = () => {
  const { layoutURL } = useContext(CustomizerContext);
  const [data, setData] = useState([]);
  useEffect(() => {
    let isMounted = true;
    if (isMounted) {
      axios.get(UserEditTableAPI).then((res) => setData(res.data));
    }
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <Fragment>
      <Card>
        <CardHeader>
          <H4 attrH4={{ className: 'card-title mb-0' }}>{UsersTableTitle}</H4>
          <div className='card-options'>
            <a className='card-options-collapse' href='#javascript' data-toggle='card-collapse'>
              <i className='fe fe-chevron-up'></i>
            </a>
            <a className='card-options-remove' href='#javascript' data-toggle='card-remove'>
              <i className='fe fe-x'></i>
            </a>
          </div>
        </CardHeader>
        <div className='table-responsive edit-table'>
          <table className='table card-table table-vcenter text-nowrap'>
            <thead>
              <tr>
                {UsersTableHeader.map((items, i) => (
                  <th key={i}>{items}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((items, i) => (
                <tr key={i}>
                  <td>
                    <Link className='theme-text' to={`/app/project/project-list/${layoutURL}`}>
                      {items.projectName}
                    </Link>
                  </td>
                  <td>{items.date}</td>
                  <td>
                    <span className='status-icon bg-success'></span>
                    {items.status}
                  </td>
                  <td>{items.price}</td>
                  <td className='text-end'>
                    <Btn attrBtn={{ color: 'primary', size: 'sm' }}>
                      <i className='fa fa-pencil'></i> {Edit}
                    </Btn>
                    <Btn attrBtn={{ className: 'focuse-none', color: 'transparent', size: 'sm' }}>
                      <i className='fa fa-link'></i> {Update}
                    </Btn>
                    <Btn attrBtn={{ color: 'danger', size: 'sm' }}>
                      <i className='fa fa-trash'></i> {Delete}
                    </Btn>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </Fragment>
  );
};

export default UserTable;

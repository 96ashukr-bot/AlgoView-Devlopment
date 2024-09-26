import React, { Fragment, useEffect, useState } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Input, Button } from 'reactstrap';
import { fetchUserData } from '../../../Services/Authentication';
import './UserList.css';

const UserList = () => {
  const [userData, setUserData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortColumn, setSortColumn] = useState('id');
  const [sortDirection, setSortDirection] = useState('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const getUserData = async () => {
      try {
        const data = await fetchUserData();
        setUserData(data);
      } catch (error) {
        console.error("Error fetching user data:", error);
      } finally {
        setLoading(false);
      }
    };
    
    getUserData(); 
  }, []);

  const sortData = (data) => {
    return [...data].sort((a, b) => {
      if (a[sortColumn] < b[sortColumn]) {
        return sortDirection === 'asc' ? -1 : 1;
      }
      if (a[sortColumn] > b[sortColumn]) {
        return sortDirection === 'asc' ? 1 : -1;
      }
      return 0;
    });
  };

  const handleSort = (column) => {
    const direction = sortColumn === column && sortDirection === 'asc' ? 'desc' : 'asc';
    setSortColumn(column);
    setSortDirection(direction);
  };

  const filteredUsers = userData.filter(user =>
    (user.firstName && user.firstName.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (user.lastName && user.lastName.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (user.email && user.email.toLowerCase().includes(searchQuery.toLowerCase())) || 
    (user.phoneNumber && user.phoneNumber.toLowerCase().includes(searchQuery.toLowerCase())) || 
    (user.role && user.role.toLowerCase().includes(searchQuery.toLowerCase()))
  );
  

  const indexOfLastUser = currentPage * itemsPerPage;
  const indexOfFirstUser = indexOfLastUser - itemsPerPage;
  const currentUsers = sortData(filteredUsers).slice(indexOfFirstUser, indexOfLastUser);

  const totalPages = Math.ceil(filteredUsers.length / itemsPerPage);

  if (loading) {
    return <div>Loading user data...</div>;
  }

  return (
    <Fragment>
      <Col sm="12">
        <Card style={{ marginTop: '80px' }}>
          <CardHeader>
            <div className="d-flex justify-content-between align-items-center">
              <div>
                <h3>User List</h3>
                <span>{"Below is the list of users along with their details."}</span>
              </div>
              <div>
                <Input 
                  type="text" 
                  placeholder="Search..." 
                  value={searchQuery} 
                  onChange={(e) => setSearchQuery(e.target.value)} 
                  style={{ width: '200px', display: 'inline-block', marginRight: '10px' }} 
                />
                <Button color="primary">Search</Button>
              </div>
            </div>
          </CardHeader>
          <div className="card-block row" style={{ height: '100%' }}>
            <Col sm="12" style={{ height: '100%' }}>
              <div className="table-responsive" style={{ height: '100%' }}>
                <Table style={{ height: '100%' }}>
                  <thead>
                    <tr>
                      <th onClick={() => handleSort('id')}>ID</th>
                      <th onClick={() => handleSort('firstName')}>First Name</th>
                      <th onClick={() => handleSort('lastName')}>Last Name</th>
                      <th onClick={() => handleSort('email')}>Email</th>
                      <th onClick={() => handleSort('phoneNumber')}>Phone Number</th>
                      <th onClick={() => handleSort('role')}>Role</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentUsers.map(user => (
                      <tr key={user.id}>
                        <td>{user.id}</td>
                        <td>{user.firstName}</td>
                        <td>{user.lastName}</td>
                        <td>{user.email}</td>
                        <td>{user.phoneNumber}</td>
                        <td>{user.role}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
              {/* Pagination */}
              <div className="d-flex justify-content-end">
                <Pagination>
                  <PaginationItem disabled={currentPage === 1}>
                    <PaginationLink onClick={() => setCurrentPage(currentPage - 1)}>
                      Previous
                    </PaginationLink>
                  </PaginationItem>
                  {[...Array(totalPages)].map((_, index) => (
                    <PaginationItem key={index} active={index + 1 === currentPage}>
                      <PaginationLink onClick={() => setCurrentPage(index + 1)}>
                        {index + 1}
                      </PaginationLink>
                    </PaginationItem>
                  ))}
                  <PaginationItem disabled={currentPage === totalPages}>
                    <PaginationLink onClick={() => setCurrentPage(currentPage + 1)}>
                      Next
                    </PaginationLink>
                  </PaginationItem>
                </Pagination>
              </div>
            </Col>
          </div>
        </Card>
      </Col>
    </Fragment>
  );
};

export default UserList;

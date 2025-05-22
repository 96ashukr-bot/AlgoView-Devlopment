import React, { Fragment, useEffect, useState } from 'react';
import { Col, Card, Table, CardHeader, Pagination, PaginationItem, PaginationLink, Input } from 'reactstrap';
import { FaTrashAlt, FaArrowUp, FaArrowDown, FaEye, FaPencilAlt } from 'react-icons/fa';
import { ToastContainer, toast } from 'react-toastify';
import Swal from 'sweetalert2';
import 'react-toastify/dist/ReactToastify.css';
import './UserList.css';
import { RotatingLines } from 'react-loader-spinner';
import { fetchUserData, deleteUser, updateUser, SearchUsers } from '../../../../../Services/Authentication';
import { useNavigate } from 'react-router-dom';

const UserList = () => {
  const [userData, setUserData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [totalPages, setTotalPages] = useState([]);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();
  const [pageBatch, setPageBatch] = useState(0);
  const [sortConfig, setSortConfig] = useState({ key: '', direction: '' });
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    if (searchQuery) {
      handleSearch();
    } else {
      getUserData();
    }

    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    handleResize();
    window.addEventListener('resize', handleResize);

    return () => window.removeEventListener('resize', handleResize);

  }, [currentPage, itemsPerPage, searchQuery]);

  const pagesPerBatch = isMobile ? 2 : 4;

  const getUserData = async () => {
    try {
      setLoading(true);
      const data = await fetchUserData(currentPage, itemsPerPage);

      if (data.results && data.results.length > 0) {
        setUserData(data.results); // Directly store the paginated data.
        setTotalPages(Math.ceil(data.count / itemsPerPage));
      } else {
        setUserData([]); // Handle empty pages.
      }
    } catch (err) {
      console.error("Error fetching data:", err);
      setError("Failed to load data.");
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    try {
      setLoading(true);
      const data = await SearchUsers(searchQuery);
      setUserData(data.results);
      setTotalPages(Math.ceil(data.count / itemsPerPage));
    } catch (err) {
      console.error("Error searching data:", err);
      setError("Failed to search data.");
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = async (userId) => {
    console.log('Edit user with ID:', userId);
    const updatedData = {};
    try {
      const response = await updateUser(userId, updatedData);
      console.log('User updated successfully:', response);
    } catch (error) {
      console.error('Error updating user:', error);
    }
    navigate(`/subadmin/userlist/edit-user/${userId}`);
  };

  const handleViewClient = (userId) => {
    console.log('View client:', userId);
    navigate(`/subadmin/userlist/view/${userId}`);
  };

  const handleDelete = async (userId) => {
    const result = await Swal.fire({
      title: 'Are you sure want to delete the user ?',
      text: 'You won\'t be able to revert this!',
      icon: 'warning',
      showCancelButton: true,
      confirmButtonColor: '#3085d6',
      cancelButtonColor: '#d33',
      confirmButtonText: 'Yes, delete it!'
    });

    if (result.isConfirmed) {
      try {
        await deleteUser(userId);
        setUserData(userData.filter(user => user.id !== userId));
        toast.success('User Deleted Successfully!');
        getUserData();
        console.log(`User with ID ${userId} deleted.`);
      } catch (error) {
        console.error(`Error deleting user with ID ${userId}:`, error);
        toast.error('Error deleting user.');
      }
    }
  };

  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });

    const sortedUsers = [...userData].sort((a, b) => {
      if (a[key] < b[key]) return direction === 'asc' ? -1 : 1;
      if (a[key] > b[key]) return direction === 'asc' ? 1 : -1;
      return 0;
    });
    setUserData(sortedUsers);
  };

  const filteredUsers = Array.isArray(userData) ? userData.filter((user) => {
    const query = searchQuery.toLowerCase();
    return (
      (user.firstName && user.firstName.toLowerCase().includes(query)) ||
      (user.lastName && user.lastName.toLowerCase().includes(query)) ||
      (user.email && user.email.toLowerCase().includes(query)) ||
      (user.phoneNumber && user.phoneNumber.includes(query)) ||
      (user.role && user.role.name && user.role.name.toLowerCase().includes(query)) ||
      (user.client_count && user.client_count.toString().includes(query))
    );
  }) : [];

  const indexOfLastUser = currentPage * itemsPerPage;
  const indexOfFirstUser = indexOfLastUser - itemsPerPage;

  let currentUsers = filteredUsers;

  if (currentPage === 1 && filteredUsers.length > itemsPerPage) {
    const extraItem = filteredUsers[filteredUsers.length - 1];
    currentUsers = [extraItem, ...currentUsers.slice(0, itemsPerPage - 1)];
  }

  const handlePreviousBatch = () => {
    if (pageBatch > 0) setPageBatch(pageBatch - 1);
  };

  const handleNextBatch = () => {
    const maxBatch = Math.ceil(totalPages / pagesPerBatch) - 1;
    if (pageBatch < maxBatch) setPageBatch(pageBatch + 1);
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handlePrevious = () => {
    if (currentPage > 1) setCurrentPage(currentPage - 1);
  };

  const handleNext = () => {
    if (currentPage < totalPages) setCurrentPage(currentPage + 1);
  };

  const startPage = pageBatch * pagesPerBatch + 1;
  const endPage = Math.min(startPage + pagesPerBatch - 1, totalPages);
  const pages = Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i);

  return (
    <Fragment>
      <ToastContainer />
      <Col sm="12">
        <Card style={{ marginTop: '80px' }}>
          <CardHeader>
            <div className="d-flex justify-content-between align-items-center custom-responsive-style">
              <div>
                <h3>User List</h3>
                {/* <span>Below is the list of users along with their details.</span> */}
              </div>
              <div>
                <button className="btn btn-primary search-btn-clr custom-responsive-style-btn" onClick={() => navigate('/subadmin/userlist/addusers')} style={{ marginRight: '20px' }}>
                  Add New User
                </button>
                <Input
                  type="text"
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{ width: '200px', display: 'inline-block', marginRight: '10px' }}
                />
                <button className="btn btn-primary search-btn-clr" onClick={handleSearch}>Search</button>
              </div>
            </div>
          </CardHeader>
          <div className="card-block row" style={{ height: '100%' }}>
            <Col sm="12" style={{ height: '100%' }}>
              <div className="table-responsive" style={{ height: '100%' }}>
                <Table style={{ height: '100%' }}>
                  <thead>
                    <tr>
                      <th className="custom-col-design">S.NO</th>
                      <th className="custom-col-design sortable" onClick={() => handleSort('firstName')}>
                        First Name
                        <FaArrowUp className="sort-arrow-left" />
                        <FaArrowDown className="sort-arrow-right" />
                      </th>
                      <th className="custom-col-design sortable" onClick={() => handleSort('lastName')}>
                        Last Name
                        <FaArrowUp className="sort-arrow-left" />
                        <FaArrowDown className="sort-arrow-right" />
                      </th>
                      <th className="custom-col-design sortable" onClick={() => handleSort('email')}>
                        Email
                        <FaArrowUp className="sort-arrow-left" />
                        <FaArrowDown className="sort-arrow-right" />
                      </th>
                      <th className="custom-col-design sortable" onClick={() => handleSort('phoneNumber')}>
                        Phone Number
                        <FaArrowUp className="sort-arrow-left" />
                        <FaArrowDown className="sort-arrow-right" />
                      </th>
                      <th className="custom-col-design sortable" onClick={() => handleSort('role')}>
                        Role
                        <FaArrowUp className="sort-arrow-left" />
                        <FaArrowDown className="sort-arrow-right" />
                      </th>
                      <th className="custom-col-design sortable" onClick={() => handleSort('client_count')}>
                        Client Count
                        <FaArrowUp className="sort-arrow-left" />
                        <FaArrowDown className="sort-arrow-right" />
                      </th>
                      <th className="custom-col-design">View</th>
                      <th className="custom-col-design">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loading ? (
                      <tr>
                        <td colSpan="9" style={{ textAlign: 'center', height: '100px' }}>
                          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
                            <RotatingLines
                              strokeColor="#283F7B"
                              strokeWidth="4"
                              animationDuration="0.75"
                              width="50"
                              visible={true}
                            />
                          </div>
                        </td>
                      </tr>
                    ) : currentUsers.length > 0 ? (
                      currentUsers.map((user, index) => (
                        <tr key={user.id}>
                          <td>{indexOfFirstUser + index + 1}</td>
                          <td>{user.firstName}</td>
                          <td>{user.lastName}</td>
                          <td>{user.email}</td>
                          <td>{user.phoneNumber}</td>
                          <td>{user.role?.name}</td>
                          <td>{user.client_count} Clients</td>
                          <td>
                            <FaEye
                              onClick={() => handleViewClient(user.id)}
                              style={{ cursor: 'pointer', marginLeft: '10px', fontSize: '18px' }}
                            />
                          </td>
                          <td>
                            <FaPencilAlt
                              style={{ cursor: 'pointer', color: '#6d62e7', marginRight: '10px' }}
                              onClick={() => handleEdit(user.id)}
                            />
                            <FaTrashAlt
                              style={{ cursor: 'pointer', color: '#ef3636' }}
                              onClick={() => handleDelete(user.id)}
                            />
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="9" className="text-center">No Users Found.</td>
                      </tr>
                    )}
                  </tbody>

                </Table>

              </div>
              <div className={`d-flex justify-content-end align-items-center ${isMobile ? 'gap-0' : 'gap-0'} custom-pagi-style`}>
                <p className="mb-0 me-2">Rows per page</p>
                <Input
                  type="select"
                  value={itemsPerPage}
                  onChange={(e) => {
                    setItemsPerPage(parseInt(e.target.value));
                    setCurrentPage(1); // Reset to page 1 when changing items per page
                  }}
                  style={{ width: '80px' }}
                  className="me-3"
                >
                  <option value="10">10</option>
                  <option value="25">25</option>
                  <option value="50">50</option>
                </Input>
                <Pagination>
                  {/* Previous button */}
                  <PaginationItem disabled={currentPage === 1}>
                    <PaginationLink previous onClick={handlePrevious}>
                      {isMobile ? 'Pre' : 'Previous'}
                    </PaginationLink>
                  </PaginationItem>

                  {/* '<' arrow */}
                  {pageBatch > 0 && (
                    <PaginationItem>
                      <PaginationLink onClick={handlePreviousBatch}>&lt;</PaginationLink>
                    </PaginationItem>
                  )}

                  {/* Page numbers */}
                  {pages.map((page) => (
                    <PaginationItem active={page === currentPage} key={page}>
                      <PaginationLink onClick={() => handlePageChange(page)}>{page}</PaginationLink>
                    </PaginationItem>
                  ))}

                  {/* '>' arrow */}
                  {endPage < totalPages && (
                    <PaginationItem>
                      <PaginationLink onClick={handleNextBatch}>&gt;</PaginationLink>
                    </PaginationItem>
                  )}

                  {/* Next button */}
                  <PaginationItem disabled={currentPage === totalPages}>
                    <PaginationLink next onClick={handleNext}>
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
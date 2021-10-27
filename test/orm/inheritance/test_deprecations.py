from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import testing
from sqlalchemy.orm import relationship
from sqlalchemy.testing import eq_
from sqlalchemy.testing import fixtures
from sqlalchemy.testing.assertions import expect_deprecated_20
from sqlalchemy.testing.fixtures import fixture_session
from sqlalchemy.testing.schema import Column
from sqlalchemy.testing.schema import Table
from ._poly_fixtures import _Polymorphic
from ._poly_fixtures import _PolymorphicAliasedJoins
from ._poly_fixtures import _PolymorphicJoins
from ._poly_fixtures import _PolymorphicPolymorphic
from ._poly_fixtures import _PolymorphicUnions
from ._poly_fixtures import Company
from ._poly_fixtures import Engineer
from ._poly_fixtures import Manager
from ._poly_fixtures import Paperwork
from ._poly_fixtures import Person


aliased_jp_dep = (
    r"The ``aliased`` and ``from_joinpoint`` keyword arguments "
    r"to Query.join\(\) are deprecated"
)


class _PolymorphicTestBase(fixtures.NoCache):
    __backend__ = True
    __dialect__ = "default_enhanced"

    @classmethod
    def setup_mappers(cls):
        super(_PolymorphicTestBase, cls).setup_mappers()
        global people, engineers, managers, boss
        global companies, paperwork, machines
        people, engineers, managers, boss, companies, paperwork, machines = (
            cls.tables.people,
            cls.tables.engineers,
            cls.tables.managers,
            cls.tables.boss,
            cls.tables.companies,
            cls.tables.paperwork,
            cls.tables.machines,
        )

    @classmethod
    def insert_data(cls, connection):
        super(_PolymorphicTestBase, cls).insert_data(connection)

        global all_employees, c1_employees, c2_employees
        global c1, c2, e1, e2, e3, b1, m1
        c1, c2, all_employees, c1_employees, c2_employees = (
            cls.c1,
            cls.c2,
            cls.all_employees,
            cls.c1_employees,
            cls.c2_employees,
        )
        e1, e2, e3, b1, m1 = cls.e1, cls.e2, cls.e3, cls.b1, cls.m1

    def test_join_from_polymorphic_flag_aliased_one(self):
        sess = fixture_session()
        with expect_deprecated_20(aliased_jp_dep):
            eq_(
                sess.query(Person)
                .order_by(Person.person_id)
                .join(Person.paperwork, aliased=True)
                .filter(Paperwork.description.like("%review%"))
                .all(),
                [b1, m1],
            )

    def test_join_from_polymorphic_flag_aliased_two(self):
        sess = fixture_session()
        with expect_deprecated_20(aliased_jp_dep):
            eq_(
                sess.query(Person)
                .order_by(Person.person_id)
                .join(Person.paperwork, aliased=True)
                .filter(Paperwork.description.like("%#2%"))
                .all(),
                [e1, m1],
            )

    def test_join_from_with_polymorphic_flag_aliased_one(self):
        sess = fixture_session()
        with expect_deprecated_20(aliased_jp_dep):
            eq_(
                sess.query(Person)
                .with_polymorphic(Manager)
                .join(Person.paperwork, aliased=True)
                .filter(Paperwork.description.like("%review%"))
                .all(),
                [b1, m1],
            )

    def test_join_from_with_polymorphic_flag_aliased_two(self):
        sess = fixture_session()
        with expect_deprecated_20(aliased_jp_dep):
            eq_(
                sess.query(Person)
                .with_polymorphic([Manager, Engineer])
                .order_by(Person.person_id)
                .join(Person.paperwork, aliased=True)
                .filter(Paperwork.description.like("%#2%"))
                .all(),
                [e1, m1],
            )

    def test_join_to_polymorphic_flag_aliased(self):
        sess = fixture_session()
        with expect_deprecated_20(aliased_jp_dep):
            eq_(
                sess.query(Company)
                .join(Company.employees, aliased=True)
                .filter(Person.name == "vlad")
                .one(),
                c2,
            )

    def test_polymorphic_any_flag_alias_two(self):
        sess = fixture_session()
        # test that the aliasing on "Person" does not bleed into the
        # EXISTS clause generated by any()
        any_ = Company.employees.any(Person.name == "wally")
        with expect_deprecated_20(aliased_jp_dep):
            eq_(
                sess.query(Company)
                .join(Company.employees, aliased=True)
                .filter(Person.name == "dilbert")
                .filter(any_)
                .all(),
                [c1],
            )

    def test_join_from_polymorphic_flag_aliased_three(self):
        sess = fixture_session()
        with expect_deprecated_20(aliased_jp_dep):
            eq_(
                sess.query(Engineer)
                .order_by(Person.person_id)
                .join(Person.paperwork, aliased=True)
                .filter(Paperwork.description.like("%#2%"))
                .all(),
                [e1],
            )


class PolymorphicTest(_PolymorphicTestBase, _Polymorphic):
    pass


class PolymorphicPolymorphicTest(
    _PolymorphicTestBase, _PolymorphicPolymorphic
):
    pass


class PolymorphicUnionsTest(_PolymorphicTestBase, _PolymorphicUnions):
    pass


class PolymorphicAliasedJoinsTest(
    _PolymorphicTestBase, _PolymorphicAliasedJoins
):
    pass


class PolymorphicJoinsTest(_PolymorphicTestBase, _PolymorphicJoins):
    pass


class RelationshipToSingleTest(
    testing.AssertsCompiledSQL, fixtures.MappedTest
):
    __dialect__ = "default"

    @classmethod
    def define_tables(cls, metadata):
        Table(
            "employees",
            metadata,
            Column(
                "employee_id",
                Integer,
                primary_key=True,
                test_needs_autoincrement=True,
            ),
            Column("name", String(50)),
            Column("manager_data", String(50)),
            Column("engineer_info", String(50)),
            Column("type", String(20)),
            Column("company_id", Integer, ForeignKey("companies.company_id")),
        )

        Table(
            "companies",
            metadata,
            Column(
                "company_id",
                Integer,
                primary_key=True,
                test_needs_autoincrement=True,
            ),
            Column("name", String(50)),
        )

    @classmethod
    def setup_classes(cls):
        class Company(cls.Comparable):
            pass

        class Employee(cls.Comparable):
            pass

        class Manager(Employee):
            pass

        class Engineer(Employee):
            pass

        class JuniorEngineer(Engineer):
            pass

    def test_of_type_aliased_fromjoinpoint(self):
        Company, Employee, Engineer = (
            self.classes.Company,
            self.classes.Employee,
            self.classes.Engineer,
        )
        companies, employees = self.tables.companies, self.tables.employees

        self.mapper_registry.map_imperatively(
            Company, companies, properties={"employee": relationship(Employee)}
        )
        self.mapper_registry.map_imperatively(
            Employee, employees, polymorphic_on=employees.c.type
        )
        self.mapper_registry.map_imperatively(
            Engineer, inherits=Employee, polymorphic_identity="engineer"
        )

        sess = fixture_session()

        with expect_deprecated_20(aliased_jp_dep):
            self.assert_compile(
                sess.query(Company).outerjoin(
                    Company.employee.of_type(Engineer),
                    aliased=True,
                    from_joinpoint=True,
                ),
                "SELECT companies.company_id AS companies_company_id, "
                "companies.name AS companies_name FROM companies "
                "LEFT OUTER JOIN employees AS employees_1 ON "
                "companies.company_id = employees_1.company_id "
                "AND employees_1.type IN ([POSTCOMPILE_type_1])",
            )

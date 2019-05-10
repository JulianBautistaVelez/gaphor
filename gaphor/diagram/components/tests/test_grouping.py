from gaphor import UML
from gaphor.tests import TestCase
from .. import NodeItem, ComponentItem, SubsystemItem, ArtifactItem
from ...usecases import UseCaseItem


class NodesGroupTestCase(TestCase):
    """
    Nodes grouping tests.
    """

    def test_grouping(self):
        """Test node within another node composition
        """
        n1 = self.create(NodeItem, UML.Node)
        n2 = self.create(NodeItem, UML.Node)

        self.group(n1, n2)

        self.assertTrue(n2.subject in n1.subject.nestedNode)
        self.assertFalse(n1.subject in n2.subject.nestedNode)

    def test_ungrouping(self):
        """Test decomposition of component from node
        """
        n1 = self.create(NodeItem, UML.Node)
        n2 = self.create(NodeItem, UML.Node)

        self.group(n1, n2)
        self.ungroup(n1, n2)

        self.assertFalse(n2.subject in n1.subject.nestedNode)
        self.assertFalse(n1.subject in n2.subject.nestedNode)


class NodeComponentGroupTestCase(TestCase):
    def test_grouping(self):
        """Test component within node composition
        """
        n = self.create(NodeItem, UML.Node)
        c = self.create(ComponentItem, UML.Component)

        self.group(n, c)

        self.assertEqual(1, len(n.subject.ownedAttribute))
        self.assertEqual(1, len(n.subject.ownedConnector))
        self.assertEqual(1, len(c.subject.ownedAttribute))
        self.assertEqual(2, len(self.kindof(UML.ConnectorEnd)))

        a1 = n.subject.ownedAttribute[0]
        a2 = c.subject.ownedAttribute[0]

        self.assertTrue(a1.isComposite)
        self.assertTrue(a1 in n.subject.part)

        connector = n.subject.ownedConnector[0]
        self.assertTrue(connector.end[0].role is a1)
        self.assertTrue(connector.end[1].role is a2)

    def test_ungrouping(self):
        """Test decomposition of component from node
        """
        n = self.create(NodeItem, UML.Node)
        c = self.create(ComponentItem, UML.Component)

        query = self.group(n, c)
        query = self.ungroup(n, c)

        self.assertEqual(0, len(n.subject.ownedAttribute))
        self.assertEqual(0, len(c.subject.ownedAttribute))
        self.assertEqual(0, len(self.kindof(UML.Property)))
        self.assertEqual(0, len(self.kindof(UML.Connector)))
        self.assertEqual(0, len(self.kindof(UML.ConnectorEnd)))


class NodeArtifactGroupTestCase(TestCase):
    def test_grouping(self):
        """Test artifact within node deployment
        """
        n = self.create(NodeItem, UML.Node)
        a = self.create(ArtifactItem, UML.Artifact)

        self.group(n, a)

        self.assertEqual(1, len(n.subject.deployment))
        self.assertTrue(n.subject.deployment[0].deployedArtifact[0] is a.subject)

    def test_ungrouping(self):
        """Test removal of artifact from node
        """
        n = self.create(NodeItem, UML.Node)
        a = self.create(ArtifactItem, UML.Artifact)

        query = self.group(n, a)
        query = self.ungroup(n, a)

        self.assertEqual(0, len(n.subject.deployment))
        self.assertEqual(0, len(self.kindof(UML.Deployment)))


class SubsystemUseCaseGroupTestCase(TestCase):
    def test_grouping(self):
        """Test adding an use case to a subsystem
        """
        s = self.create(SubsystemItem, UML.Component)
        uc1 = self.create(UseCaseItem, UML.UseCase)
        uc2 = self.create(UseCaseItem, UML.UseCase)

        self.group(s, uc1)
        self.assertEqual(1, len(uc1.subject.subject))
        self.group(s, uc2)
        self.assertEqual(1, len(uc2.subject.subject))

        # Classifier.useCase is not navigable to UseCase
        # self.assertEqual(2, len(s.subject.useCase))

    def test_grouping_with_namespace(self):
        """Test adding an use case to a subsystem (with namespace)
        """
        s = self.create(SubsystemItem, UML.Component)
        uc = self.create(UseCaseItem, UML.UseCase)

        # manipulate namespace
        c = self.element_factory.create(UML.Class)
        attribute = self.element_factory.create(UML.Property)
        c.ownedAttribute = attribute

        self.group(s, uc)
        self.assertEqual(1, len(uc.subject.subject))
        self.assertTrue(s.subject.namespace is not uc.subject)

    def test_ungrouping(self):
        """Test removal of use case from subsystem
        """
        s = self.create(SubsystemItem, UML.Component)
        uc1 = self.create(UseCaseItem, UML.UseCase)
        uc2 = self.create(UseCaseItem, UML.UseCase)

        self.group(s, uc1)
        self.group(s, uc2)

        self.ungroup(s, uc1)
        self.assertEqual(0, len(uc1.subject.subject))
        # Classifier.useCase is not navigable to UseCase
        # self.assertEqual(1, len(s.subject.useCase))

        self.ungroup(s, uc2)
        self.assertEqual(0, len(uc2.subject.subject))
        # Classifier.useCase is not navigable to UseCase
        # self.assertEqual(0, len(s.subject.useCase))

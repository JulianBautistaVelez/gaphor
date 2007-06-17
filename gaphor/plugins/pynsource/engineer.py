# vim:sw=4:et

"""The code reverse engineer.
"""

from zope import component
from gaphor import UML
from gaphor.diagram import items
from gaphor.core import inject
from gaphor.diagram.interfaces import IConnect

from pynsource import PySourceAsText

BASE_CLASSES = ('object', 'type', 'dict', 'list', 'tuple', 'int', 'float')

class Engineer(object):
    """
    The Engineer class will create a Gaphor model based on a list of Python
    files.
    """

    element_factory = inject('element_factory')
    diagram_layout = inject('diagram_layout')

    def process(self, files=None):

        # these are tuples between class names.
        #self.associations_generalisation = []
        #self.associations_composition = []

        p = PySourceAsText()
        self.parser = p

        if files:
            #u = PythonToJava(None, treatmoduleasclass=0, verbose=0)
            for f in files:
                # Build a shape with all attrs and methods, and prepare association dict
                p.Parse(f)

        print p
        
        try:
            self._root_package = self.element_factory.lselect(lambda e: isinstance(e, UML.Package) and not e.namespace)[0]
        except IndexError:
            pass # running as test?

        for m in p.modulemethods:
            print 'ModuleMethod:', m

        # Step 0: create a diagram to put the newly created elements on
        self.diagram = self.element_factory.create(UML.Diagram)
        self.diagram.name = 'New classes'
        self.diagram.package = self._root_package

        # Step 1: create the classes
        for name, clazz in p.classlist.items():
            print type(clazz), dir(clazz)
            self._create_class(clazz, name)
            
        # Create generalization relationships:
        for name, clazz in p.classlist.items():
            self._create_generalization(clazz)
        
        # Create attributes (and associations) on the classes
        for name, clazz in p.classlist.items():
            self._create_attributes(clazz)

        # Create operations
        for name, clazz in p.classlist.items():
            self._create_methods(clazz)

        self.diagram_layout.layout_diagram(self.diagram)

    def _create_class(self, clazz, name):
        c = self.element_factory.create(UML.Class)
        c.name = name
        c.package = self.diagram.namespace
        ci = self.diagram.create(items.ClassItem)
        ci.subject = c
        clazz.gaphor_class = c
        clazz.gaphor_class_item = ci

    def _create_generalization(self, clazz):
        if not clazz.ismodulenotrealclass:
            for superclassname in clazz.classesinheritsfrom:
                if superclassname in BASE_CLASSES:
                    continue
                try:
                    superclass = self.parser.classlist[superclassname].gaphor_class
                    superclass_item = self.parser.classlist[superclassname].gaphor_class_item
                except KeyError, e:
                    print 'No class found named', superclassname
                    others = self.element_factory.lselect(lambda e: isinstance(e, UML.Class) and e.name == superclassname)
                    if others:
                        superclass = others[0]
                        print 'Found class in factory: %s' % superclass.name
                        superclass_item = self.diagram.create(items.ClassItem)
                        superclass_item.subject = superclass
                    else:
                        continue
                # Finally, create the generalization relationship
                print 'Creating Generalization for %s' % clazz, superclass
                gen = self.element_factory.create(UML.Generalization)
                gen.general = superclass
                gen.specific = clazz.gaphor_class
                geni = self.diagram.create(items.GeneralizationItem)
                geni.subject = gen
                
                adapter = component.queryMultiAdapter((superclass_item, geni), IConnect)
                assert adapter
                handle = geni.handles()[0]
                adapter.connect(handle, handle.x, handle.y)
                #clazz.gaphor_class_item.connect_handle(geni.handles[-1])
                adapter = component.queryMultiAdapter((clazz.gaphor_class_item, geni), IConnect)
                assert adapter
                handle = geni.handles()[-1]
                adapter.connect(handle, handle.x, handle.y)

    def _create_attributes(self, clazz):
        for attrobj in clazz.attrs:
            # TODO: Check object type and figure out if it should be an
            # attribute or an association.
            self._create_attribute(clazz, attrobj)

    def _create_methods(self, clazz):
        for adef in clazz.defs:
            op = self.element_factory.create(UML.Operation)
            op.name = adef
            clazz.gaphor_class.ownedOperation = op

    def _find_class_by_name(self, classname):
        try:
            superclass = self.parser.classlist[classname].gaphor_class
            superclass_item = self.parser.classlist[classname].gaphor_class_item
        except KeyError, e:
            print 'No class found named', classname
            others = self.element_factory.lselect(lambda e: isinstance(e, UML.Class) and e.name == classname)
            if others:
                superclass = others[0]
                print 'Found class in factory: %s' % superclass.name
                superclass_item = self.diagram.create(items.ClassItem)
                superclass_item.subject = superclass
            else:
                return None, None
        return superclass, superclass_item

    def _visibility(self, attrname):
        if attrname.startswith('__'):
            return 'private'
        elif attrname.startswith('_'):
            return 'protected'
        return 'public'

    def _create_attribute(self, clazz, attr):
        static = False
        many = False
        if 'static' in attr.attrtype:
            static = True
        if 'many' in attr.attrtype:
            many = True
        compositescreated = self.parser.GetCompositeClassesForAttr(attr.attrname, clazz)
        tail_type = None
        if compositescreated:
            tail_type, tail_type_item = self._find_class_by_name(compositescreated[0])

        if tail_type:
            # Create an association:
            #print "%s %s <@>----> %s" % (attr.attrname, static, str(compositescreated))
            # The property on the tail of the association (tail_end) is owned
            # by the class connected on the head_end (head_type)
            head_type = clazz.gaphor_class
            head_type_item = clazz.gaphor_class_item

            relation = self.element_factory.create(UML.Association)
            head_end = self.element_factory.create(UML.Property)
            head_end.lowerValue = self.element_factory.create(UML.LiteralSpecification)
            tail_end = self.element_factory.create(UML.Property)
            tail_end.name = attr.attrname
            tail_end.visibility = self._visibility(attr.attrname)
            tail_end.aggregation = 'composite'
            tail_end.lowerValue = self.element_factory.create(UML.LiteralSpecification)
            relation.package = self.diagram.namespace
            relation.memberEnd = head_end
            relation.memberEnd = tail_end
            head_end.type = head_type
            tail_end.type = tail_type
            head_type.ownedAttribute = tail_end
            tail_type.ownedAttribute = head_end

            # Now create the diagram item:
            association = self.diagram.create(items.AssociationItem)

            # First connect one handle:
            #head_type_item.connect_handle(association.handles[0])
            adapter = component.queryMultiAdapter((head_type_item, association), IConnect)
            assert adapter
            handle = association.handles()[0]
            adapter.connect(handle, handle.x, handle.y)

            
            # Now the subject
            association.subject = relation
            association.set_property('head-subject', head_end)
            association.set_property('tail-subject', tail_end)

            # Connecting the other handle last will avoid a lookup for
            # an Association. in stead the association applied as subject
            # is used.
            #tail_type_item.connect_handle(association.handles[-1])
            adapter = component.queryMultiAdapter((tail_type_item, association), IConnect)
            assert adapter
            handle = association.handles()[-1]
            adapter.connect(handle, handle.x, handle.y)

        else:
            # Create a simple attribute:
            #print "%s %s" % (attr.attrname, static)
            prop = self.element_factory.create(UML.Property)
            prop.name = attr.attrname
            prop.visibility = self._visibility(attr.attrname)
            prop.isStatic = static
            clazz.gaphor_class.ownedAttribute = prop
        #print many
        import pprint
        pprint.pprint(attr)
        #print dir(attr)
